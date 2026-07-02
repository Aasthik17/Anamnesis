from typing import List, Dict, Tuple
from collections import defaultdict
from anamnesis.memory.client import MemoryClient
from anamnesis.memory.schemas import MemoryRecord, MemoryType, CodeRuleMemory

class MemoryConsolidator:
    """
    [COGNEE PRIMITIVE: memify / reflect]
    Consolidates near-duplicate or related memories into higher-level
    team rules and coding conventions.
    """
    def __init__(self, client: MemoryClient):
        self.client = client

    def reflect(self) -> List[CodeRuleMemory]:
        """
        Analyze all bug memories, cluster related issues across files,
        and generate consolidated rules.
        """
        memories = self.client.list_memories(MemoryType.BUG_FIX)
        if not memories:
            return []

        # Group bug memories by common keywords / root cause signatures
        clusters: Dict[str, List[MemoryRecord]] = defaultdict(list)
        
        for mem in memories:
            text = (mem.title + " " + mem.content).lower()
            if "null" in text or "none" in text or "unchecked" in text or "api" in text or "response" in text:
                clusters["Null-check external API responses & handle empty returns"].append(mem)
            elif "validation" in text or "input" in text or "bound" in text:
                clusters["Validate incoming requests and sanitize inputs in service handlers"].append(mem)
            elif "timeout" in text or "retry" in text or "connection" in text:
                clusters["Configure explicit timeouts and exponential backoff on remote HTTP calls"].append(mem)
            else:
                clusters["General error handling convention"].append(mem)

        created_rules: List[CodeRuleMemory] = []
        existing_rules = self.client.get_rules()
        existing_titles = {r.title for r in existing_rules}

        for rule_title, mem_list in clusters.items():
            if len(mem_list) >= 1 and rule_title not in existing_titles:
                affected_files = list({m.file_path for m in mem_list if m.file_path})
                domain = "services" if any("service" in (f or "") for f in affected_files) else "general"
                
                rule = CodeRuleMemory(
                    rule_title=rule_title,
                    description=(
                        f"Consolidated rule from {len(mem_list)} reported issue(s). "
                        f"Always ensure safe handling and check response status before accessing nested fields."
                    ),
                    domain=domain,
                    origin_memory_ids=[m.id for m in mem_list],
                    provenance_files=affected_files,
                    confidence=min(0.7 + (len(mem_list) * 0.1), 0.98)
                )
                
                self.client.remember_rule(rule)
                created_rules.append(rule)

        # Trigger Cognee memify native primitive if available
        if self.client._init_cognee_if_needed():
            try:
                import asyncio
                import cognee
                if hasattr(cognee, "memify"):
                    asyncio.run(cognee.memify())
            except Exception:
                pass

        return created_rules
