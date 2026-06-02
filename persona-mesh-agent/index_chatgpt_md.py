#!/usr/bin/env python3
"""One-time indexer for C:\CHATGPT markdown files into the vector store."""

import sys
sys.path.insert(0, str(__file__).rsplit("\\", 1)[0])

from agent_core.memory_vector import VectorMemory

vm = VectorMemory()
if not vm.is_available:
    print("Vector store not available — check LlamaIndex install.")
    sys.exit(1)

print("Indexing C:\\CHATGPT ...")
result = vm.index_path(r"C:\CHATGPT", recursive=False)
print(f"Done. Indexed: {result['indexed']}  Skipped: {result['skipped']}")
