"""Seed gallery data with stock images of Cape Verde airports and CTA team."""

import asyncio
import sys
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from database import db, ensure_schema, close_pool  # noqa: E402

ALBUMS = [
    {
        "id": "album-aeroportos",
        "title": "Aeroportos de Cabo Verde",
        "description": "Os aeroportos internacionais e domesticos que servem o arquipelago de Cabo Verde, onde os nossos controladores garantem a seguranca de cada voo.",
        "order": 1,
        "photos": [
            {
                "url": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?q=80&w=2074&auto=format&fit=crop",
                "caption": "Vista aerea - Aproximacao ao arquipelago",
            },
            {
                "url": "https://images.unsplash.com/photo-1570710891163-6d3b5c47248b?q=80&w=2070&auto=format&fit=crop",
                "caption": "Terminal aeroportuario - Operacoes diarias",
            },
            {
                "url": "https://images.unsplash.com/photo-1474302770737-173ee21bab63?q=80&w=2070&auto=format&fit=crop",
                "caption": "Pista de aterragem ao por do sol",
            },
            {
                "url": "https://images.unsplash.com/photo-1556388158-158ea5ccacbd?q=80&w=2070&auto=format&fit=crop",
                "caption": "Aeronave na plataforma de estacionamento",
            },
            {
                "url": "https://images.unsplash.com/photo-1529074717022-8ff6a8c70c6b?q=80&w=2070&auto=format&fit=crop",
                "caption": "Operacoes noturnas no aeroporto",
            },
            {
                "url": "https://images.unsplash.com/photo-1464037866556-6812c9d1c72e?q=80&w=2070&auto=format&fit=crop",
                "caption": "Vista panoramica da pista",
            },
        ],
    },
    {
        "id": "album-torre-controlo",
        "title": "Torre de Controlo e Operacoes",
        "description": "O ambiente de trabalho dos controladores de trafego aereo - onde tecnologia de ponta e pericia humana se encontram para garantir a seguranca dos ceus.",
        "order": 2,
        "photos": [
            {
                "url": "https://images.unsplash.com/photo-1540962351504-03099e0a754b?q=80&w=2070&auto=format&fit=crop",
                "caption": "Torre de controlo - Centro de operacoes",
            },
            {
                "url": "https://images.unsplash.com/photo-1566057816200-1690e1f5a251?q=80&w=2070&auto=format&fit=crop",
                "caption": "Tecnologia radar - Vigilancia aerea",
            },
            {
                "url": "https://images.unsplash.com/photo-1610094273627-f97d5bc5084e?q=80&w=2070&auto=format&fit=crop",
                "caption": "Sistemas de comunicacao e navegacao",
            },
            {
                "url": "https://images.unsplash.com/photo-1559128010-7c1ad6e1b6a5?q=80&w=2070&auto=format&fit=crop",
                "caption": "Vista da torre ao entardecer",
            },
            {
                "url": "https://images.unsplash.com/photo-1583511655826-05700d52f4d9?q=80&w=2070&auto=format&fit=crop",
                "caption": "Equipamento de controlo aereo",
            },
        ],
    },
    {
        "id": "album-cabo-verde",
        "title": "Cabo Verde - O Nosso Pais",
        "description": "As belas paisagens do arquipelago de Cabo Verde - as ilhas que os nossos controladores ajudam a conectar com o mundo.",
        "order": 3,
        "photos": [
            {
                "url": "https://images.unsplash.com/photo-1672856181212-b5b5a0065a08?q=80&w=2070&auto=format&fit=crop",
                "caption": "Paisagem costeira de Cabo Verde",
            },
            {
                "url": "https://images.unsplash.com/photo-1651666990398-5585ad2c9eac?q=80&w=2070&auto=format&fit=crop",
                "caption": "Praia paradisiaca - Ilha do Sal",
            },
            {
                "url": "https://images.unsplash.com/photo-1502920514313-52581002a659?q=80&w=2070&auto=format&fit=crop",
                "caption": "Vista aerea das ilhas do Atlantico",
            },
            {
                "url": "https://images.unsplash.com/photo-1580060839134-75a5edca2e99?q=80&w=2070&auto=format&fit=crop",
                "caption": "Montanhas vulcanicas de Cabo Verde",
            },
            {
                "url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=2070&auto=format&fit=crop",
                "caption": "Costa atlantica ao por do sol",
            },
            {
                "url": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?q=80&w=2070&auto=format&fit=crop",
                "caption": "Oceano Atlantico visto do arquipelago",
            },
        ],
    },
    {
        "id": "album-equipa",
        "title": "A Nossa Equipa",
        "description": "Os profissionais dedicados que formam a ACCTA - controladores de trafego aereo, tecnicos e staff administrativo ao servico da aviacao cabo-verdiana.",
        "order": 4,
        "photos": [
            {
                "url": "https://images.unsplash.com/photo-1522071820081-009f0129c71c?q=80&w=2070&auto=format&fit=crop",
                "caption": "Equipa ACCTA em reuniao de trabalho",
            },
            {
                "url": "https://images.unsplash.com/photo-1600880292203-757bb62b4baf?q=80&w=2070&auto=format&fit=crop",
                "caption": "Colaboracao entre profissionais",
            },
            {
                "url": "https://images.unsplash.com/photo-1552664730-d307ca884978?q=80&w=2070&auto=format&fit=crop",
                "caption": "Sessao de formacao continua",
            },
            {
                "url": "https://images.unsplash.com/photo-1531482615713-2afd69097998?q=80&w=2070&auto=format&fit=crop",
                "caption": "Discussao tecnica entre controladores",
            },
            {
                "url": "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?q=80&w=2070&auto=format&fit=crop",
                "caption": "Apresentacao na assembleia geral",
            },
        ],
    },
]


async def seed_gallery():
    await ensure_schema()

    # Clear existing gallery data
    await db.gallery_albums.delete_many({})
    await db.gallery_photos.delete_many({})

    for album_data in ALBUMS:
        photos = album_data.pop("photos")
        album_data["photo_count"] = len(photos)
        album_data["cover_url"] = photos[0]["url"] if photos else ""
        album_data["created_at"] = datetime.now(timezone.utc).isoformat()

        await db.gallery_albums.insert_one(album_data)

        for i, photo in enumerate(photos):
            photo_doc = {
                "id": str(uuid.uuid4()),
                "album_id": album_data["id"],
                "url": photo["url"],
                "caption": photo["caption"],
                "order": i,
                "uploaded_by": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            await db.gallery_photos.insert_one(photo_doc)

    print(f"Seeded {len(ALBUMS)} albums with photos")
    await close_pool()


if __name__ == "__main__":
    asyncio.run(seed_gallery())
