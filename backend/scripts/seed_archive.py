"""Import reviewed records and optionally build dense vectors."""
import argparse
import asyncio
from config import settings
from db.database import Archive, load_records
from services.embeddings import embed_text, model_signature


async def run(path, embed=False):
    archive = Archive(settings.ARCHIVE_PATH)
    count = archive.import_records(load_records(path))
    print(f'Imported {count} reviewed assertions into {settings.ARCHIVE_PATH}')
    if embed:
        if settings.EMBEDDING_PROVIDER == 'none':
            raise SystemExit('Set EMBEDDING_PROVIDER=gemini or local before indexing.')
        for row in archive.records():
            import json
            doc = json.loads(row['document'])
            vector = await embed_text(doc['claim_text'] + '\n' + doc['snippet'], query=False)
            if vector is None:
                raise SystemExit('No embedding provider is configured.')
            archive.set_vector(row['id'], model_signature(), vector)
        print(f'Indexed vectors using {model_signature()}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', nargs='?', default=str(settings.ARCHIVE_SEED))
    parser.add_argument('--embed', action='store_true')
    args = parser.parse_args()
    asyncio.run(run(args.path, args.embed))
