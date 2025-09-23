import epg_zap2it

# Check what's actually in the EPG data
epg_data = epg_zap2it.fetch_gracenote_epg()

print("September 23rd Evening Shows (8 PM):")
for show in epg_data:
    if show.get('date') == '2025-09-23' and '8:' in show.get('time', ''):
        print(f"  {show['time']}: {show['title']} on {show['channel']}")

print("\nAll Jeopardy-related shows:")
jeopardy_shows = [s for s in epg_data if 'jeopardy' in s['title'].lower()]
for show in jeopardy_shows:
    print(f"  {show['title']} on {show['channel']} at {show['time']} ({show['date']})")

print(f"\nTotal shows found: {len(epg_data)}")
print(f"Jeopardy shows found: {len(jeopardy_shows)}")

print("\nShows on KXAN (36.1):")
kxan_shows = [s for s in epg_data if s.get('channel_number') == '36.1']
for show in kxan_shows:
    print(f"  {show['time']}: {show['title']}")