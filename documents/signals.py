from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Document, DocumentChunk
from .embedding import generate_embedding


def simple_chunk_text(text, chunk_size=500):
    """
    Split text into fixed-size chunks.
    """
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    return chunks


@receiver(post_save, sender=Document)
def create_document_chunks(sender, instance, created, **kwargs):
    if created:
        try:
            file_path = instance.file.path

            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

            chunks = simple_chunk_text(text)

            for chunk in chunks:
                embedding = generate_embedding(chunk)

                DocumentChunk.objects.create(
                    document=instance,
                    content=chunk,
                    embedding=embedding
                )

            print(f"✅ Created {len(chunks)} chunks with embeddings")

        except Exception as e:
            print("❌ Error while processing document:", e)