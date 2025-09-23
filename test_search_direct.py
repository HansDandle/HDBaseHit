#!/usr/bin/env python3
"""
Test the new smart search directly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from epg_zap2it import search_epg_for_show

def test_search():
    print("🧪 Testing enhanced search function...")
    
    # Test the search function directly
    results = search_epg_for_show("oregon football game", days=7)
    
    print(f"\n📊 Search Results Summary:")
    print(f"   Total matches: {len(results)}")
    
    for i, result in enumerate(results[:5]):  # Show top 5
        score = result.get('match_score', 0)
        print(f"   {i+1}. {result.get('title')} (Score: {score:.1f})")
        print(f"      {result.get('channel')} at {result.get('time')} on {result.get('date')}")

if __name__ == "__main__":
    test_search()