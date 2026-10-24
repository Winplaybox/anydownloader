import asyncio
import os
import sys
from pathlib import Path

# Add project root and backend to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "backend"))

from backend.platform_registry import registry
from backend.engines.registry import engine_registry
from backend.engines.base import ExtractContext
from backend.normalizer import normalize_raw_result

async def run_selftest():
    print("=== OVD Downloader Self-Test Suite ===")
    results = {}
    
    for p in registry.platforms:
        pid = p.get("id")
        tier = p.get("tier", "A")
        test_urls = p.get("selfTestUrls", {})
        
        if not test_urls:
            print(f"[{pid}] No self-test URLs configured. Skipping.")
            continue
            
        print(f"\nTesting platform '{pid}' (Tier {tier})...")
        platform_ok = True
        
        for ctype, test_url in test_urls.items():
            # Support env variable substitution (e.g. ${SELFTEST_YT_VIDEO})
            if test_url.startswith("${") and test_url.endswith("}"):
                env_key = test_url[2:-1]
                test_url = os.environ.get(env_key, "")
            
            if not test_url:
                print(f"  - [{ctype}] No URL provided. Skipping.")
                continue
                
            print(f"  - [{ctype}] URL: {test_url}")
            ctx = ExtractContext(url=test_url, content_type=ctype, platform_id=pid, timeout=15.0)
            
            try:
                raw = await engine_registry.execute_chain(test_url, p.get("routes", {}), ctype, ctx)
                norm = normalize_raw_result(raw, p, ctype)
                item_count = len(norm.videos) + len(norm.images) + len(norm.audios) + len(norm.thumbnails)
                print(f"    SUCCESS: Extracted {item_count} items by engine '{raw.engine_id}' (Title: '{norm.title[:40]}...')")
            except Exception as e:
                print(f"    FAILURE: {e}")
                platform_ok = False
        
        status = "ok" if platform_ok else "degraded"
        results[pid] = status
        registry.set_status(pid, status)
        print(f"  -> Platform '{pid}' status: {status.upper()}")

    print("\n=== Summary ===")
    for pid, st in results.items():
        print(f"{pid:15}: {st}")

if __name__ == "__main__":
    asyncio.run(run_selftest())
