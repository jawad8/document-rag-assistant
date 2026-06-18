from django.test import SimpleTestCase

from .signals import simple_chunk_text


class DocumentChunkingTests(SimpleTestCase):
    def test_splits_text_into_fixed_size_chunks(self):
        chunks = simple_chunk_text("abcdefghij", chunk_size=4)

        self.assertEqual(chunks, ["abcd", "efgh", "ij"])

    def test_empty_text_returns_no_chunks(self):
        self.assertEqual(simple_chunk_text(""), [])
