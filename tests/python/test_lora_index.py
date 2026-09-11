import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path


if "folder_paths" not in sys.modules:
    fake_folder_paths = types.ModuleType("folder_paths")
    fake_folder_paths.get_filename_list = lambda _kind: []
    fake_folder_paths.get_full_path = lambda _kind, _name: None
    fake_folder_paths.get_folder_paths = lambda _kind: []
    sys.modules["folder_paths"] = fake_folder_paths

from modules.lora_index import LoraIndex  # noqa: E402


class LoraIndexTests(unittest.TestCase):
    def test_preserves_weight_and_activation_prompt_while_normalizing_local_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            index = LoraIndex(Path(directory) / "cache.json")
            prompt, weight = index._split_leading_lora_reference(
                "<lora:wrong_remote:0.8> incoth, (incase:0.6)"
            )
            entry = {
                "stem": "styles/incoth",
                "relative_name": "styles/incoth.safetensors",
                "display_name": "InCoth Style",
                "base_model": "Illustrious",
                "trained_words": ["incoth", "incase"],
                "trigger_prompt": prompt,
                "lora_weight": weight,
            }

            public = index._public_entry(entry)

            self.assertEqual(prompt, "incoth, (incase:0.6)")
            self.assertEqual(weight, "0.8")
            self.assertEqual(
                public["insert_text"],
                "<lora:styles/incoth:0.8> incoth, (incase:0.6)",
            )
            self.assertIn("incoth", public["search_terms"])
            self.assertIn("incase", public["search_terms"])

    def test_correct_local_reference_round_trips_without_losing_activation_text(self):
        with tempfile.TemporaryDirectory() as directory:
            index = LoraIndex(Path(directory) / "cache.json")
            prompt, weight = index._split_leading_lora_reference(
                "<lora:incoth:1> incoth, (incase:0.6)"
            )
            public = index._public_entry({
                "stem": "incoth",
                "relative_name": "incoth.safetensors",
                "display_name": "incoth",
                "base_model": "Illustrious",
                "trained_words": ["incoth", "incase"],
                "trigger_prompt": prompt,
                "lora_weight": weight,
            })

            self.assertEqual(
                public["insert_text"],
                "<lora:incoth:1> incoth, (incase:0.6)",
            )

    def test_reads_loratags_master_database_by_subfolder(self):
        database = {
            "styles/incase": {
                "incoth.safetensors": "<lora:incoth:1> incoth, (incase:0.6)"
            }
        }
        self.assertEqual(
            LoraIndex._master_prompt_for(
                [database],
                "styles/incase/incoth.safetensors",
            ),
            "<lora:incoth:1> incoth, (incase:0.6)",
        )

    def test_collects_all_sha256_hashes_from_multi_file_civitai_version(self):
        first = "A" * 64
        second = "B" * 64
        payload = {
            "files": [
                {"hashes": {"SHA256": first}},
                {"hashes": {"SHA256": second}},
            ]
        }
        self.assertEqual(LoraIndex._payload_sha256s(payload), {first, second})

    def test_generic_training_base_does_not_prevent_civitai_family_lookup(self):
        index = LoraIndex("unused.json")
        extracted = index._extract_metadata({
            "ss_base_model_version": "sdxl_base_v1-0",
            "activation_text": "incoth",
        })
        entry = {
            "base_model": extracted["base_model"],
            "base_model_fallback": extracted["base_model_fallback"],
            "trigger_prompt": extracted["trigger_prompt"],
        }

        self.assertEqual(entry["base_model"], "")
        self.assertEqual(entry["base_model_fallback"], "sdxl_base_v1-0")
        self.assertTrue(LoraIndex._needs_civitai(entry))

    def test_refresh_uses_local_sidecar_without_civitai_when_metadata_is_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lora_file = root / "styles" / "incoth.safetensors"
            lora_file.parent.mkdir(parents=True)
            # A tiny non-safetensors body is enough: sidecar metadata should make
            # a network lookup unnecessary, and the malformed safetensors header
            # is safely ignored.
            lora_file.write_bytes(b"not-a-real-safetensors-file")
            sidecar = lora_file.with_suffix(".metadata.json")
            sidecar.write_text(json.dumps({
                "model_name": "InCoth Style",
                "base_model": "Illustrious",
                "civitai": {"trainedWords": ["incoth", "incase"]},
            }), encoding="utf-8")

            import folder_paths
            old_names = folder_paths.get_filename_list
            old_full = folder_paths.get_full_path
            old_roots = folder_paths.get_folder_paths
            folder_paths.get_filename_list = lambda kind: ["styles/incoth.safetensors"] if kind == "loras" else []
            folder_paths.get_full_path = lambda kind, name: str(root / name) if kind == "loras" else None
            folder_paths.get_folder_paths = lambda _kind: []
            try:
                index = LoraIndex(root / "cache.json")
                index._civitai_lookup = lambda _hashes: self.fail("Civitai lookup should not run")
                [row] = index.refresh()
            finally:
                folder_paths.get_filename_list = old_names
                folder_paths.get_full_path = old_full
                folder_paths.get_folder_paths = old_roots

            self.assertEqual(row["base_model"], "Illustrious")
            self.assertEqual(row["display_name"], "InCoth Style")
            self.assertEqual(row["trained_words"], ["incoth", "incase"])
            self.assertEqual(
                row["insert_text"],
                "<lora:styles/incoth:1> incoth, incase",
            )


if __name__ == "__main__":
    unittest.main()
