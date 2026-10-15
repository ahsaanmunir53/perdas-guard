"""Builds every service once from settings. Routers and agents get them from here."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from app.config import Settings
from app.llm.base import LLM
from app.packs import PackRegistry
from app.services.cases import CaseService, Dispatcher
from app.services.content import ContentService
from app.services.evidence import HmacSigner, KmsSigner, Signer
from app.services.network import GraphStore, MemoryGraphStore
from app.services.pipeline import CheckPipeline
from app.services.privacy import Hasher, Masker, SensitiveDataProtection
from app.services.recruiters import BUNDLED_SAMPLE, RecruiterDirectory
from app.services.security import ModelArmorScreen, screen_locally
from app.services.vault import BlobStore, EvidenceVault, GcsBlobStore, MemoryBlobStore
from app.storage import DocStore, FirestoreStore, MemoryStore

log = logging.getLogger(__name__)


@dataclass
class Container:
    settings: Settings
    store: DocStore
    packs: PackRegistry
    recruiters: RecruiterDirectory
    hasher: Hasher
    graph: GraphStore
    masker: Masker
    llm: LLM
    pipeline: CheckPipeline
    cases: CaseService
    vault: EvidenceVault
    content: ContentService
    signer: Signer


def _llm(settings: Settings) -> LLM:
    if settings.llm_backend == "gemini":
        from app.llm.gemini import GeminiLLM

        return GeminiLLM(settings)
    from app.llm.fake import FakeLLM

    return FakeLLM()


def _graph(settings: Settings, hasher: Hasher) -> GraphStore:
    if settings.graph_backend == "spanner":
        from app.services.network_spanner import SpannerGraphStore

        return SpannerGraphStore(settings.google_cloud_project, settings.spanner_instance, settings.spanner_database, hasher)
    return MemoryGraphStore(hasher)


def build_container(settings: Settings, dispatcher: Dispatcher | None = None) -> Container:
    if settings.is_prod:
        problems = settings.validate_for_prod()
        if problems:
            raise RuntimeError("Refusing to start in prod: " + "; ".join(problems))

    store: DocStore = FirestoreStore(settings.google_cloud_project) if settings.store_backend == "firestore" else MemoryStore()
    blobs: BlobStore = GcsBlobStore(settings.gcs_bucket) if settings.gcs_bucket else MemoryBlobStore()
    packs = PackRegistry(Path(settings.packs_dir) if settings.packs_dir else None)

    recruiters = RecruiterDirectory()
    if settings.recruiters_csv:
        n = recruiters.load_file(Path(settings.recruiters_csv), source="official_list")
        log.info("Loaded %d licensed recruiters from the official list", n)
    else:
        n = recruiters.load_file(BUNDLED_SAMPLE, source="sample")
        log.warning("Loaded %d FICTIONAL sample recruiters; import the official list before launch", n)

    hasher = Hasher(settings.hash_salt)
    graph = _graph(settings, hasher)
    sdp = SensitiveDataProtection(settings.google_cloud_project) if settings.use_sensitive_data_protection else None
    masker = Masker(sdp)
    screen = ModelArmorScreen(settings.model_armor_template).screen if settings.model_armor_template else screen_locally
    signer: Signer = KmsSigner(settings.kms_key_version) if settings.kms_key_version else HmacSigner(settings.evidence_signing_key)
    llm = _llm(settings)

    pipeline = CheckPipeline(
        llm=llm, packs=packs, recruiters=recruiters, graph=graph, masker=masker, store=store, screen=screen
    )
    content = ContentService(store, packs, llm)
    replayed = content.replay_approved()
    if replayed:
        log.info("Replayed %d approved content updates", replayed)

    return Container(
        settings=settings,
        store=store,
        packs=packs,
        recruiters=recruiters,
        hasher=hasher,
        graph=graph,
        masker=masker,
        llm=llm,
        pipeline=pipeline,
        cases=CaseService(store, packs, dispatcher),
        vault=EvidenceVault(store, blobs, signer),
        content=content,
        signer=signer,
    )
