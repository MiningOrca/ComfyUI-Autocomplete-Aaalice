from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Iterable

import folder_paths


LOGGER = logging.getLogger(__name__)

CACHE_VERSION = 3
CIVITAI_BULK_URL = "https://civitai.com/api/v1/model-versions/by-hash"
CIVITAI_BATCH_SIZE = 100
SAFETENSORS_MAX_HEADER = 32 * 1024 * 1024
LEADING_LORA_REFERENCE_RE = re.compile(r"^\s*<lora:([^>]+)>\s*", re.IGNORECASE)
ANY_LORA_REFERENCE_RE = re.compile(r"<lora:[^>]+>", re.IGNORECASE)
PROMPT_WEIGHT_RE = re.compile(r"^\(?\s*(.*?)\s*:\s*-?[0-9]+(?:\.[0-9]+)?\s*\)?$")
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class LoraIndex:
    """Incremental index of local LoRAs and their activation metadata."""

    def __init__(self, cache_file: str | os.PathLike[str]):
        self.cache_file = Path(cache_file)
        self._lock = threading.Lock()

    def refresh(self, force: bool = False) -> list[dict[str, Any]]:
        """Rescan local LoRAs, enrich changed entries, persist and return UI rows."""
        with self._lock:
            cached_entries = {} if force else self._load_cache().get("entries", {})
            master_databases = self._load_loratags_master()
            next_entries: dict[str, dict[str, Any]] = {}
            civitai_pending: list[tuple[str, str]] = []

            for raw_name in folder_paths.get_filename_list("loras"):
                full_path = folder_paths.get_full_path("loras", raw_name)
                if not full_path or not os.path.isfile(full_path):
                    continue

                path = Path(full_path)
                stat = path.stat()
                relative_name = raw_name.replace("\\", "/")
                sidecars = self._sidecar_signature(path)
                master_prompt = self._master_prompt_for(master_databases, relative_name)
                previous = cached_entries.get(relative_name, {})

                file_unchanged = (
                    previous.get("size") == stat.st_size
                    and previous.get("mtime_ns") == stat.st_mtime_ns
                )
                unchanged = (
                    not force
                    and file_unchanged
                    and previous.get("sidecars") == sidecars
                    and previous.get("master_prompt", "") == master_prompt
                )
                if unchanged:
                    next_entries[relative_name] = previous
                    continue

                entry = self._build_local_entry(
                    relative_name=relative_name,
                    path=path,
                    size=stat.st_size,
                    mtime_ns=stat.st_mtime_ns,
                    sidecar_signature=sidecars,
                    master_prompt=master_prompt,
                    previous=previous,
                    file_unchanged=file_unchanged,
                )
                next_entries[relative_name] = entry

                if self._needs_civitai(entry) and not entry.get("civitai_checked"):
                    sha256 = entry.get("sha256", "")
                    if not SHA256_RE.fullmatch(sha256):
                        sha256 = self._sha256(path)
                        entry["sha256"] = sha256
                    civitai_pending.append((relative_name, sha256))

            self._enrich_from_civitai(next_entries, civitai_pending)
            self._save_cache(next_entries)
            return [
                self._public_entry(next_entries[name])
                for name in sorted(next_entries, key=str.casefold)
            ]

    def _build_local_entry(
        self,
        relative_name: str,
        path: Path,
        size: int,
        mtime_ns: int,
        sidecar_signature: dict[str, list[int]],
        master_prompt: str,
        previous: dict[str, Any],
        file_unchanged: bool,
    ) -> dict[str, Any]:
        stem = os.path.splitext(relative_name)[0].replace("\\", "/")
        display_name = ""
        base_model = ""
        base_model_fallback = ""
        trained_words: list[str] = []
        activation_prompt = ""
        reference_weight = "1"
        metadata_sources: list[str] = []
        sha256 = previous.get("sha256", "") if file_unchanged else ""
        civitai_checked = bool(previous.get("civitai_checked")) if file_unchanged else False

        if master_prompt:
            activation_prompt, master_weight = self._split_leading_lora_reference(master_prompt)
            if master_weight:
                reference_weight = master_weight
            trained_words = self._search_terms_from_prompt(activation_prompt)
            metadata_sources.append("loratags")

        for sidecar in self._sidecar_paths(path):
            if not sidecar.is_file():
                continue
            payload = self._read_json(sidecar)
            if not isinstance(payload, dict):
                continue

            extracted = self._extract_metadata(payload)
            display_name = display_name or extracted["model_name"]
            base_model = base_model or extracted["base_model"]
            base_model_fallback = base_model_fallback or extracted["base_model_fallback"]
            sha256 = sha256 or extracted["sha256"]
            if not trained_words:
                trained_words = extracted["trained_words"]
            if not activation_prompt and extracted["trigger_prompt"]:
                activation_prompt, extracted_weight = self._split_leading_lora_reference(
                    extracted["trigger_prompt"]
                )
                if extracted_weight:
                    reference_weight = extracted_weight
            metadata_sources.append(sidecar.name)

        if path.suffix.lower() == ".safetensors":
            extracted = self._extract_metadata(self._read_safetensors_metadata(path))
            display_name = display_name or extracted["model_name"]
            base_model = base_model or extracted["base_model"]
            base_model_fallback = base_model_fallback or extracted["base_model_fallback"]
            if not trained_words:
                trained_words = extracted["trained_words"]
            if not activation_prompt and extracted["trigger_prompt"]:
                activation_prompt, extracted_weight = self._split_leading_lora_reference(
                    extracted["trigger_prompt"]
                )
                if extracted_weight:
                    reference_weight = extracted_weight
            if any((extracted["model_name"], extracted["base_model"], extracted["trigger_prompt"])):
                metadata_sources.append("safetensors")

        trained_words = self._unique_strings(trained_words)
        if not activation_prompt and trained_words:
            activation_prompt = ", ".join(trained_words)
        elif activation_prompt and not trained_words:
            trained_words = self._search_terms_from_prompt(activation_prompt)

        return {
            "relative_name": relative_name,
            "stem": stem,
            "display_name": display_name or Path(stem).name,
            "base_model": base_model,
            "base_model_fallback": base_model_fallback,
            "trained_words": trained_words,
            "trigger_prompt": self._clean_prompt_edges(activation_prompt),
            "lora_weight": reference_weight or "1",
            "size": size,
            "mtime_ns": mtime_ns,
            "sidecars": sidecar_signature,
            "master_prompt": master_prompt,
            "sha256": sha256.upper() if SHA256_RE.fullmatch(sha256) else "",
            "civitai_checked": civitai_checked,
            "metadata_sources": self._unique_strings(metadata_sources),
        }

    @staticmethod
    def _needs_civitai(entry: dict[str, Any]) -> bool:
        return not entry.get("base_model") or not entry.get("trigger_prompt")

    def _enrich_from_civitai(
        self,
        entries: dict[str, dict[str, Any]],
        pending: list[tuple[str, str]],
    ) -> None:
        if not pending:
            return

        hash_to_names: dict[str, list[str]] = {}
        for relative_name, sha256 in pending:
            if SHA256_RE.fullmatch(sha256):
                hash_to_names.setdefault(sha256.upper(), []).append(relative_name)

        hashes = list(hash_to_names)
        for offset in range(0, len(hashes), CIVITAI_BATCH_SIZE):
            batch = hashes[offset : offset + CIVITAI_BATCH_SIZE]
            try:
                payloads = self._civitai_lookup(batch)
            except (OSError, ValueError, urllib.error.URLError) as error:
                LOGGER.warning("LoRA Civitai lookup skipped: %s", error)
                continue

            for sha256 in batch:
                for relative_name in hash_to_names.get(sha256, []):
                    entries[relative_name]["civitai_checked"] = True

            for payload in payloads:
                # A model version can contain several files. The hash that caused
                # the bulk lookup is not guaranteed to be the first file in the
                # response, so match against every SHA256 advertised by Civitai.
                matched_hashes = self._payload_sha256s(payload) & set(batch)
                if not matched_hashes:
                    continue
                extracted = self._extract_metadata(payload)
                for matched_hash in matched_hashes:
                    for relative_name in hash_to_names.get(matched_hash, []):
                        entry = entries[relative_name]
                        if extracted["model_name"] and entry.get("display_name") == Path(entry["stem"]).name:
                            entry["display_name"] = extracted["model_name"]
                        if extracted["base_model"] and not entry.get("base_model"):
                            entry["base_model"] = extracted["base_model"]
                        if extracted["trained_words"] and not entry.get("trained_words"):
                            entry["trained_words"] = extracted["trained_words"]
                        if not entry.get("trigger_prompt") and extracted["trained_words"]:
                            entry["trigger_prompt"] = ", ".join(extracted["trained_words"])
                        if "civitai" not in entry["metadata_sources"]:
                            entry["metadata_sources"].append("civitai")

    @staticmethod
    def _civitai_lookup(hashes: list[str]) -> list[dict[str, Any]]:
        request = urllib.request.Request(
            CIVITAI_BULK_URL,
            data=json.dumps(hashes).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "ComfyUI-Autocomplete-Aaalice/LoRA-index",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - fixed endpoint
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, list):
            raise ValueError("Civitai bulk hash response is not a list")
        return [item for item in payload if isinstance(item, dict)]

    @staticmethod
    def _payload_sha256s(payload: dict[str, Any]) -> set[str]:
        files = payload.get("files")
        if not isinstance(files, list):
            return set()
        result: set[str] = set()
        for file_data in files:
            if not isinstance(file_data, dict):
                continue
            hashes = file_data.get("hashes")
            if isinstance(hashes, dict):
                sha256 = str(hashes.get("SHA256") or "").strip()
                if SHA256_RE.fullmatch(sha256):
                    result.add(sha256.upper())
        return result

    def _public_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        stem = str(entry.get("stem", ""))
        trigger_prompt = self._clean_prompt_edges(str(entry.get("trigger_prompt", "")))
        weight = self._normalize_weight(entry.get("lora_weight"))
        reference = f"<lora:{stem}:{weight}>"
        trained_words = self._unique_strings(entry.get("trained_words", []))
        search_terms = self._unique_strings([
            str(entry.get("display_name", "")),
            stem,
            Path(stem).name,
        ])
        activation_tags = self._activation_tags(trigger_prompt, trained_words)
        return {
            "name": stem,
            "filename": entry.get("relative_name", ""),
            "display_name": entry.get("display_name") or Path(stem).name,
            "base_model": entry.get("base_model") or entry.get("base_model_fallback") or "Unknown",
            "trained_words": trained_words,
            "trigger_prompt": trigger_prompt,
            "search_terms": search_terms,
            "reference_insert_text": reference,
            # Kept for older frontends. It is intentionally reference-only: activation
            # tags are separate autocomplete candidates and must never be inserted as a
            # bundle when the LoRA model candidate is selected.
            "insert_text": reference,
            "activation_tags": activation_tags,
        }

    def _load_cache(self) -> dict[str, Any]:
        payload = self._read_json(self.cache_file)
        if not isinstance(payload, dict) or payload.get("version") != CACHE_VERSION:
            return {"version": CACHE_VERSION, "entries": {}}
        if not isinstance(payload.get("entries"), dict):
            payload["entries"] = {}
        return payload

    def _save_cache(self, entries: dict[str, dict[str, Any]]) -> None:
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file = self.cache_file.with_suffix(self.cache_file.suffix + ".tmp")
        with temp_file.open("w", encoding="utf-8") as file:
            json.dump({"version": CACHE_VERSION, "entries": entries}, file, ensure_ascii=False, indent=2)
        os.replace(temp_file, self.cache_file)

    @staticmethod
    def _read_json(path: Path) -> Any:
        try:
            with path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return None

    def _load_loratags_master(self) -> list[dict[str, Any]]:
        databases: list[dict[str, Any]] = []
        try:
            custom_node_roots = folder_paths.get_folder_paths("custom_nodes")
        except (KeyError, AttributeError):
            custom_node_roots = []

        for root in custom_node_roots:
            try:
                children = os.listdir(root)
            except OSError:
                continue
            for child in children:
                if "loratag" not in child.casefold():
                    continue
                payload = self._read_json(Path(root) / child / "lora_master_tags.json")
                if isinstance(payload, dict):
                    databases.append(payload)
        return databases

    @staticmethod
    def _master_prompt_for(databases: list[dict[str, Any]], relative_name: str) -> str:
        normalized = relative_name.replace("\\", "/")
        folder, filename = os.path.split(normalized)
        category = folder or "Uncategorized"
        for database in databases:
            category_data = database.get(category)
            if not isinstance(category_data, dict):
                continue
            value = category_data.get(filename)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    @staticmethod
    def _sidecar_paths(path: Path) -> list[Path]:
        stem = path.with_suffix("")
        return [
            Path(f"{stem}.metadata.json"),
            Path(f"{stem}.civitai.info"),
            Path(f"{stem}.cm-info.json"),
            Path(f"{stem}.json"),
            Path(f"{path}.json"),
        ]

    def _sidecar_signature(self, path: Path) -> dict[str, list[int]]:
        signature: dict[str, list[int]] = {}
        for sidecar in self._sidecar_paths(path):
            try:
                stat = sidecar.stat()
            except OSError:
                continue
            signature[sidecar.name] = [stat.st_size, stat.st_mtime_ns]
        return signature

    @staticmethod
    def _read_safetensors_metadata(path: Path) -> dict[str, Any]:
        try:
            with path.open("rb") as file:
                header_size_raw = file.read(8)
                if len(header_size_raw) != 8:
                    return {}
                header_size = int.from_bytes(header_size_raw, "little", signed=False)
                if header_size <= 0 or header_size > SAFETENSORS_MAX_HEADER:
                    return {}
                header = json.loads(file.read(header_size).decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return {}
        metadata = header.get("__metadata__", {}) if isinstance(header, dict) else {}
        return metadata if isinstance(metadata, dict) else {}

    def _extract_metadata(self, payload: dict[str, Any]) -> dict[str, Any]:
        trained_value = self._first_path(
            payload,
            ("trainedWords",),
            ("trained_words",),
            ("triggerWords",),
            ("trigger_words",),
            ("activation_text",),
            ("modelspec.trigger_phrase",),
            ("civitai", "trainedWords"),
            ("civitai", "trained_words"),
            ("metadata", "trainedWords"),
        )
        trained_words, trigger_prompt = self._normalize_trigger_value(trained_value)
        sha256 = self._string_value(self._first_path(
            payload,
            ("sha256",),
            ("SHA256",),
            ("hashes", "SHA256"),
        ))
        if not SHA256_RE.fullmatch(sha256):
            sha256 = ""

        return {
            "model_name": self._string_value(self._first_path(
                payload,
                ("model_name",),
                ("model", "name"),
                ("civitai", "model", "name"),
                ("modelName",),
                ("display_name",),
                ("modelspec.title",),
            )),
            "base_model": self._string_value(self._first_path(
                payload,
                ("base_model",),
                ("baseModel",),
                ("civitai", "baseModel"),
                ("civitai", "base_model"),
                ("metadata", "baseModel"),
            )),
            # Training metadata often says only "sdxl_base_v1-0" or a generic
            # architecture. Keep that as a UI fallback, but still allow a
            # Civitai hash lookup to resolve the useful family (Illustrious,
            # Pony, Anima, ...).
            "base_model_fallback": self._string_value(self._first_path(
                payload,
                ("ss_base_model_version",),
                ("modelspec.architecture",),
            )),
            "trained_words": trained_words,
            "trigger_prompt": trigger_prompt,
            "sha256": sha256.upper(),
        }

    @staticmethod
    def _first_path(payload: dict[str, Any], *paths: tuple[str, ...]) -> Any:
        for path in paths:
            current: Any = payload
            for key in path:
                if not isinstance(current, dict) or key not in current:
                    break
                current = current[key]
            else:
                if current not in (None, "", []):
                    return current
        return None

    def _normalize_trigger_value(self, value: Any) -> tuple[list[str], str]:
        if value is None:
            return [], ""
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return [], ""
            if text.startswith("["):
                try:
                    return self._normalize_trigger_value(json.loads(text))
                except json.JSONDecodeError:
                    pass
            prompt, _ = self._split_leading_lora_reference(text)
            return self._search_terms_from_prompt(prompt), prompt
        if isinstance(value, (list, tuple, set)):
            words = self._unique_strings(str(item).strip() for item in value if str(item).strip())
            return words, ", ".join(words)
        return [], ""

    @staticmethod
    def _string_value(value: Any) -> str:
        return value.strip() if isinstance(value, str) else ""

    @classmethod
    def _split_leading_lora_reference(cls, value: str) -> tuple[str, str]:
        """Remove only a leading LoRA reference and preserve its numeric weight."""
        if not value:
            return "", ""
        match = LEADING_LORA_REFERENCE_RE.match(value)
        if not match:
            return cls._clean_prompt_edges(value), ""

        payload = match.group(1).strip()
        weight = ""
        if ":" in payload:
            _, maybe_weight = payload.rsplit(":", 1)
            try:
                float(maybe_weight)
            except ValueError:
                pass
            else:
                weight = maybe_weight.strip()

        remainder = value[match.end():]
        return cls._clean_prompt_edges(remainder), weight

    @staticmethod
    def _clean_prompt_edges(value: str) -> str:
        if not value:
            return ""
        value = re.sub(r"^[\s,;]+|[\s,;]+$", "", value)
        return re.sub(r"\s{2,}", " ", value).strip()

    @classmethod
    def _activation_tags(cls, prompt: str, trained_words: Iterable[Any]) -> list[dict[str, str]]:
        """Return one autocomplete candidate per LoRA activation tag.

        ``tag`` is the searchable/plain form while ``insert_text`` preserves the
        exact activation syntax from metadata, including prompt weights such as
        ``(incase:0.6)``.
        """
        result: list[dict[str, str]] = []
        seen: set[str] = set()
        for fragment in cls._split_prompt_fragments(prompt):
            terms = cls._search_terms_from_prompt(fragment)
            if not terms:
                continue
            tag = terms[0]
            key = tag.casefold()
            if key in seen:
                continue
            seen.add(key)
            result.append({"tag": tag, "insert_text": fragment})
        for trained_word in cls._unique_strings(trained_words):
            key = trained_word.casefold()
            if key in seen:
                continue
            seen.add(key)
            result.append({"tag": trained_word, "insert_text": trained_word})
        return result

    @classmethod
    def _split_prompt_fragments(cls, prompt: str) -> list[str]:
        """Split a comma-separated prompt without breaking weighted/grouped tags."""
        prompt = ANY_LORA_REFERENCE_RE.sub("", prompt or "")
        fragments: list[str] = []
        current: list[str] = []
        depths = {"(": 0, "[": 0, "{": 0}
        closing = {")": "(", "]": "[", "}": "{"}
        quote = ""
        escaped = False
        for char in prompt:
            if escaped:
                current.append(char)
                escaped = False
                continue
            if char == "\\" and quote:
                current.append(char)
                escaped = True
                continue
            if char in {'"', "'"}:
                current.append(char)
                if quote == char:
                    quote = ""
                elif not quote:
                    quote = char
                continue
            if not quote:
                if char in depths:
                    depths[char] += 1
                elif char in closing:
                    opener = closing[char]
                    depths[opener] = max(0, depths[opener] - 1)
                elif char == "," and not any(depths.values()):
                    fragment = cls._clean_prompt_edges("".join(current))
                    if fragment:
                        fragments.append(fragment)
                    current = []
                    continue
            current.append(char)
        fragment = LoraIndex._clean_prompt_edges("".join(current))
        if fragment:
            fragments.append(fragment)
        return fragments

    @classmethod
    def _search_terms_from_prompt(cls, prompt: str) -> list[str]:
        terms: list[str] = []
        for part in cls._split_prompt_fragments(prompt):
            value = part.strip()
            if not value:
                continue
            weighted = PROMPT_WEIGHT_RE.match(value)
            if weighted:
                value = weighted.group(1).strip()
            value = value.strip("() ")
            if value:
                terms.append(value)
        return cls._unique_strings(terms)

    @staticmethod
    def _unique_strings(values: Iterable[Any]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            text = str(value).strip()
            key = text.casefold()
            if not text or key in seen:
                continue
            seen.add(key)
            result.append(text)
        return result

    @staticmethod
    def _normalize_weight(value: Any) -> str:
        text = str(value or "1").strip()
        try:
            float(text)
        except ValueError:
            return "1"
        return text

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(8 * 1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest().upper()
