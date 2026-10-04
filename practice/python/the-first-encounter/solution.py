def string_to_number_mapping(s: str) -> dict:
  seen = {}
  for ch in s:
    if ch not in seen:
      seen[ch] = s.find(ch)
  return seen
