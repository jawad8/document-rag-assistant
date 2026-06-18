from django.test import SimpleTestCase

from .views import cosine_similarity


class SimilarityTests(SimpleTestCase):
    def test_identical_vectors_have_full_similarity(self):
        self.assertAlmostEqual(cosine_similarity([1, 2], [1, 2]), 1.0)

    def test_zero_vector_is_handled_safely(self):
        self.assertEqual(cosine_similarity([0, 0], [1, 2]), 0.0)
