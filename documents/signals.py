import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .embedding import generate_embedding
from .models import Document, DocumentChunk

logger = logging.getLogger(__name__)


def simple_chunk_text(text, chunk_size=500):
    """Split text into fixed-size chunks."""
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


@receiver(post_save, sender=Document)
def create_document_chunks(sender, instance, created, **kwargs):
    if not created:
        return

    try:
        with open(instance.file.path, "r", encoding="utf-8") as source:
            text = source.read()

        chunks = simple_chunk_text(text)
        DocumentChunk.objects.bulk_create(
            [
                DocumentChunk(
                    document=instance,
                    content=chunk,
                    embedding=generate_embedding(chunk),
                )
                for chunk in chunks
            ]
        )
        logger.info("Created %s chunks for document %s", len(chunks), instance.id)
    except Exception:
        logger.exception("Could not process document %s", instance.id)
