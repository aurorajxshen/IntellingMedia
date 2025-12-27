import json
import re

# This regex captures patterns like "1:30", "12:45", "1:05:20"
# It looks for digits, a colon, and two digits (optionally with an hour prefix)
timestamp_pattern = re.compile(r'\b\d{1,2}:\d{2}(?::\d{2})?\b')

input_file = 'comments.json'
output_file = 'comments_with_timestamps.json'

print(f"Filtering {input_file} for timestamps...")
count = 0

with open(input_file, 'r', encoding='utf-8') as f_in, \
        open(output_file, 'w', encoding='utf-8') as f_out:
    for line in f_in:
        try:
            # The tool outputs line-delimited JSON
            comment = json.loads(line)
            text = comment.get('text', '')

            # If a timestamp is found in the text, save it
            if timestamp_pattern.search(text):
                json.dump(comment, f_out)
                f_out.write('\n')
                count += 1
        except json.JSONDecodeError:
            continue

print(f"Done! Found {count} comments with timestamps. Saved to {output_file}.")