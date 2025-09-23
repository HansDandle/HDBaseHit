#!/usr/bin/env python3
"""
Test the filtered search functionality to ensure it excludes preview shows
and prioritizes actual games.
"""

from epg_zap2it import search_epg_for_show

def test_utah_search():
    print("Testing 'Utah game' search with enhanced filtering...")
    results = search_epg_for_show('Utah game')
    
    print(f"\nFinal results (top 5):")
    for i, result in enumerate(results[:5], 1):
        title = result['title']
        score = result['match_score']
        print(f"  {i}. {title} - Score: {score:.1f}")
        
        # Check if this is the preview show we want to exclude
        if 'gameday' in title.lower() or 'game day' in title.lower():
            print(f"     ⚠️  Preview show detected - should have low score")
        elif any(indicator in title.lower() for indicator in ['vs', 'at', ' v ']):
            print(f"     ✅ Actual game detected - should have high score")
    
    return results

def test_wvu_search():
    print("\n" + "="*60)
    print("Testing 'WVU football' search with enhanced filtering...")
    results = search_epg_for_show('WVU football')
    
    print(f"\nFinal results (top 5):")
    for i, result in enumerate(results[:5], 1):
        title = result['title']
        score = result['match_score']
        print(f"  {i}. {title} - Score: {score:.1f}")
        
        # Check if this is the preview show we want to exclude
        if 'gameday' in title.lower() or 'game day' in title.lower():
            print(f"     ⚠️  Preview show detected - should have low score")
        elif any(indicator in title.lower() for indicator in ['vs', 'at', ' v ']):
            print(f"     ✅ Actual game detected - should have high score")
    
    return results

if __name__ == "__main__":
    print("Testing enhanced filtering logic...")
    print("Goal: Exclude preview shows, prioritize actual games")
    print("="*60)
    
    utah_results = test_utah_search()
    wvu_results = test_wvu_search()
    
    print("\n" + "="*60)
    print("SUMMARY:")
    print("- Actual games (with 'vs', 'at') should have scores 100+")
    print("- Preview shows (GameDay, etc.) should have scores under 50")
    print("- The highest scoring result should be the actual Utah vs West Virginia game")