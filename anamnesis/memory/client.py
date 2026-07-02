import os
import uuid
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from anamnesis.config import get_anamnesis_dir
from anamnesis.memory.schemas import (
    MemoryRecord, MemoryType, BugFixMemory, CodeRuleMemory, CommitMemory
)

class MemoryClient:
    """
    Client interface connecting Anamnesis CLI with Cognee memory primitives
    and local persistence metadata.
    """
    def __init__(self, repo_root: Optional[Path] = None):
        self.anamnesis_dir = get_anamnesis_dir(repo_root)
        self.store_file = self.anamnesis_dir / "memories.json"
        self._records: Dict[str, MemoryRecord] = {}
        self._load_records()
        self._cognee_initialized = False

    def _load_records(self) -> None:
        if self.store_file.exists():
            try:
                with open(self.store_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        rec = MemoryRecord(**item)
                        if rec.active:
                            self._records[rec.id] = rec
            except Exception:
                self._records = {}

    def _save_records(self) -> None:
        data = [rec.model_dump() for rec in self._records.values() if rec.active]
        with open(self.store_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _init_cognee_if_needed(self) -> bool:
        if self._cognee_initialized:
            return True
        try:
            import cognee
            from anamnesis.config import load_config
            config = load_config()

            # Set up local cognee data directory inside .anamnesis
            cognee_data_dir = str(self.anamnesis_dir / "cognee_data")
            os.environ["COGNEE_DATA_DIR"] = cognee_data_dir

            # Cloud & LLM API Key Configuration
            cognee_key = os.getenv("COGNEE_API_KEY") or config.get("cognee_api_key")
            cognee_url = os.getenv("COGNEE_API_URL") or config.get("cognee_api_url", "https://api.cognee.ai")
            llm_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or config.get("llm_api_key")

            if cognee_key:
                os.environ["COGNEE_API_KEY"] = cognee_key
                os.environ["COGNEE_API_URL"] = cognee_url
            if llm_key:
                os.environ["OPENAI_API_KEY"] = llm_key

            self._cognee_initialized = True
            return True
        except ImportError:
            return False
        except Exception:
            return False

    def remember_bug(self, bug: BugFixMemory) -> MemoryRecord:
        """
        [COGNEE PRIMITIVE: remember]
        Ingests a bug fix into memory.
        """
        mem_id = f"mem_bug_{uuid.uuid4().hex[:8]}"
        bug.id = mem_id
        content = bug.to_memory_text()

        record = MemoryRecord(
            id=mem_id,
            memory_type=MemoryType.BUG_FIX,
            title=bug.title,
            content=content,
            file_path=bug.file_path,
            metadata=bug.model_dump()
        )
        self._records[mem_id] = record
        self._save_records()

        # Push to Cognee engine
        if self._init_cognee_if_needed():
            try:
                import asyncio
                import cognee
                asyncio.run(cognee.add(content, dataset_name="anamnesis_codebase"))
                asyncio.run(cognee.cognify(dataset_name="anamnesis_codebase"))
            except Exception:
                # Local index serves as guarantee
                pass

        return record

    def remember_commit(self, commit: CommitMemory) -> MemoryRecord:
        """
        [COGNEE PRIMITIVE: remember]
        Ingests a git commit summary into memory.
        """
        mem_id = f"mem_commit_{commit.commit_hash[:7]}"
        commit.id = mem_id
        content = commit.to_memory_text()

        record = MemoryRecord(
            id=mem_id,
            memory_type=MemoryType.COMMIT,
            title=f"Commit: {commit.summary}",
            content=content,
            file_path=commit.files_changed[0] if commit.files_changed else None,
            metadata=commit.model_dump()
        )
        self._records[mem_id] = record
        self._save_records()

        if self._init_cognee_if_needed():
            try:
                import asyncio
                import cognee
                asyncio.run(cognee.add(content, dataset_name="anamnesis_codebase"))
            except Exception:
                pass

        return record

    def remember_rule(self, rule: CodeRuleMemory) -> MemoryRecord:
        """
        [COGNEE PRIMITIVE: remember / memify]
        Stores a consolidated rule.
        """
        mem_id = f"rule_{uuid.uuid4().hex[:8]}"
        rule.id = mem_id
        content = rule.to_memory_text()

        record = MemoryRecord(
            id=mem_id,
            memory_type=MemoryType.RULE,
            title=rule.rule_title,
            content=content,
            metadata=rule.model_dump()
        )
        self._records[mem_id] = record
        self._save_records()

        if self._init_cognee_if_needed():
            try:
                import asyncio
                import cognee
                asyncio.run(cognee.add(content, dataset_name="anamnesis_rules"))
            except Exception:
                pass

        return record

    def remember_doc(self, title: str, content: str, file_path: Optional[str] = None) -> MemoryRecord:
        """
        [COGNEE PRIMITIVE: remember]
        Ingests a general document, ADR, or design decision into memory.
        """
        mem_id = f"mem_doc_{uuid.uuid4().hex[:8]}"
        mem_text = f"[DOCUMENTATION] {title}\n"
        if file_path:
            mem_text += f"File Context: {file_path}\n"
        mem_text += f"Content:\n{content}\n"

        record = MemoryRecord(
            id=mem_id,
            memory_type=MemoryType.DOCUMENTATION,
            title=title,
            content=mem_text,
            file_path=file_path,
            metadata={"title": title, "file_path": file_path}
        )
        self._records[mem_id] = record
        self._save_records()

        if self._init_cognee_if_needed():
            try:
                import asyncio
                import cognee
                asyncio.run(cognee.add(mem_text, dataset_name="anamnesis_codebase"))
                asyncio.run(cognee.cognify(dataset_name="anamnesis_codebase"))
            except Exception:
                pass

        return record

    def improve(self) -> bool:
        """
        [COGNEE PRIMITIVE: improve / memify]
        Runs post-ingestion graph enrichment, edge weight adaptation, and memory pruning.
        """
        if self._init_cognee_if_needed():
            try:
                import asyncio
                import cognee
                if hasattr(cognee, "memify"):
                    asyncio.run(cognee.memify())
                asyncio.run(cognee.cognify(dataset_name="anamnesis_codebase"))
                return True
            except Exception:
                pass
        return True

    def recall(self, query: str, file_context: Optional[str] = None, top_k: int = 5) -> List[MemoryRecord]:
        """
        [COGNEE PRIMITIVE: recall]
        Surfaces relevant memories connected to query, file context, or diff signatures.
        """
        cognee_results = []
        if self._init_cognee_if_needed():
            try:
                import asyncio
                import cognee
                search_res = asyncio.run(cognee.search(query_text=query, dataset_name="anamnesis_codebase"))
                if search_res:
                    # Parse cognee search results if available
                    for res in search_res:
                        res_str = str(res)
                        for rec in self._records.values():
                            if rec.id not in [r.id for r in cognee_results] and (rec.title in res_str or rec.file_path in res_str):
                                cognee_results.append(rec)
            except Exception:
                pass

        # Graph / Vector / Keyword Fallback & Score Matching
        matched = list(cognee_results)
        query_terms = set(query.lower().replace("/", " ").replace("_", " ").split())
        
        for rec in self._records.values():
            if rec in matched or not rec.active:
                continue

            score = 0
            rec_text = (rec.content + " " + rec.title + " " + (rec.file_path or "")).lower()
            
            # File context matching
            if file_context and rec.file_path:
                norm_fc = file_context.lower().replace("\\", "/")
                norm_fp = rec.file_path.lower().replace("\\", "/")
                if norm_fc in norm_fp or norm_fp in norm_fc or Path(norm_fc).name == Path(norm_fp).name:
                    score += 5

            # Term frequency match
            for term in query_terms:
                if len(term) > 2 and term in rec_text:
                    score += 2

            if score > 0:
                matched.append((score, rec))

        # Sort combined results by score
        scored_results = []
        for item in matched:
            if isinstance(item, tuple):
                scored_results.append(item)
            else:
                scored_results.append((10, item))

        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [rec for _, rec in scored_results[:top_k]]

    def forget(self, memory_id_or_path: str) -> List[str]:
        """
        [COGNEE PRIMITIVE: forget]
        Decays or removes specified memory by ID or associated file path.
        """
        removed_ids = []
        target = memory_id_or_path.strip()

        # Check exact ID
        if target in self._records:
            self._records[target].active = False
            removed_ids.append(target)
        else:
            # Check by file path or substring
            for rec_id, rec in list(self._records.items()):
                if rec.active and (rec.file_path and target in rec.file_path or target in rec.id):
                    rec.active = False
                    removed_ids.append(rec_id)

        if removed_ids:
            self._save_records()
            if self._init_cognee_if_needed():
                try:
                    import asyncio
                    import cognee
                    # Call Cognee prune if available
                    if hasattr(cognee, "prune"):
                        asyncio.run(cognee.prune.prune_data())
                except Exception:
                    pass

        return removed_ids

    def list_memories(self, memory_type: Optional[MemoryType] = None) -> List[MemoryRecord]:
        recs = [r for r in self._records.values() if r.active]
        if memory_type:
            recs = [r for r in recs if r.memory_type == memory_type]
        return recs

    def get_rules(self) -> List[MemoryRecord]:
        return self.list_memories(MemoryType.RULE)
