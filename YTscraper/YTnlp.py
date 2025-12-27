import json
import re
from collections import Counter
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# --- CONFIGURATION ---
INPUT_FILE = 'comments_with_timestamps.json'
OUTPUT_FILE = 'dashboard_data.json'
TIME_WINDOW = 30  # Group data into 30-second buckets for the timeline

# Initialize VADER analyzer (Best for social media/comments)
analyzer = SentimentIntensityAnalyzer()


def timestamp_to_seconds(timestamp_str):
    """Converts 'MM:SS' or 'HH:MM:SS' to total seconds."""
    parts = list(map(int, timestamp_str.split(':')))
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    elif len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return 0


def extract_keywords(text):
    """Simple keyword extraction (noun phrases)."""
    blob = TextBlob(text)
    # Filter out short words and common stopwords
    stopwords = {'video', 'people', 'this', 'that', 'just', 'like', 'reaction', 'know'}
    return [word.lower() for word in blob.noun_phrases if len(word) > 3 and word.lower() not in stopwords]


def analyze_rhetorical_dimensions(text, sentiment_score):
    """Calculates the 6 dimensions for the Radar Chart (Comment Level)."""
    blob = TextBlob(text)

    # 1. Emotional Intensity (Pathos): Absolute sentiment + exclamation marks
    emotional = abs(sentiment_score) + (0.2 if '!' in text else 0)

    # 2. Subjectivity (Ethos/Self): Use of I/Me/My
    subjectivity = blob.sentiment.subjectivity

    # 3. Certainty (Tone): Looking for absolute words
    absolutes = ['always', 'never', 'definitely', 'proven', 'fact', 'wrong', 'true']
    certainty = 1.0 if any(w in text.lower() for w in absolutes) else 0.3

    # 4. Factual Density (Logos): Length + numbers + links
    has_link = 'http' in text or 'www.' in text
    has_number = any(char.isdigit() for char in text)
    factual = 0.8 if (has_link or has_number) else 0.2

    # 5. Complexity: Word count (simplified proxy)
    complexity = min(len(text.split()) / 50, 1.0)  # Cap at 1.0

    # 6. Toxicity (Estimated via low negative sentiment)
    toxicity = 1.0 if sentiment_score < -0.6 else 0.1

    return {
        "emotional": min(emotional, 1.0),
        "subjectivity": subjectivity,
        "certainty": certainty,
        "factual": factual,
        "complexity": complexity,
        "toxicity": toxicity
    }


# --- MAIN PROCESSING ---
print("Starting NLP Analysis...")

dashboard_data = {
    "timeline": {},  # Bucketed by time window
    "fact_checks": [],
    "confusion_questions": [],
    "global_topics": Counter()
}

with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            comment = json.loads(line)
            text = comment.get('text', '')
            author = comment.get('author', 'Anonymous')
            votes = int(comment.get('votes', 0))

            # 1. Extract Time
            # Regex to find the FIRST timestamp in the text
            time_match = re.search(r'(\d{1,2}:\d{2}(?:\d{2})?)', text)
            if not time_match: continue

            timestamp_str = time_match.group(1)
            seconds = timestamp_to_seconds(timestamp_str)
            bucket = (seconds // TIME_WINDOW) * TIME_WINDOW  # Floor to nearest window

            # 2. Sentiment Analysis (VADER)
            vs = analyzer.polarity_scores(text)
            compound_score = vs['compound']  # -1.0 to 1.0

            # 3. Rhetorical Analysis
            rhetoric = analyze_rhetorical_dimensions(text, compound_score)

            # 4. Detect "Context Corner" Candidates
            # Criteria: Contains URL OR ("Actually" + high votes)
            if "http" in text or ("actually" in text.lower() and votes > 5):
                dashboard_data['fact_checks'].append({
                    "time": timestamp_str,
                    "author": author,
                    "text": text[:150] + "..." if len(text) > 150 else text,
                    "votes": votes,
                    "type": "Source" if "http" in text else "Correction"
                })

            # 5. Detect "Confusion" Candidates
            # Criteria: Contains "?" and starts with Who/What/Where/Why/How
            if "?" in text and any(text.lower().startswith(q) for q in ['why', 'how', 'what', 'who']):
                dashboard_data['confusion_questions'].append({
                    "time": timestamp_str,
                    "text": text,
                    "votes": votes
                })

            # 6. Topic Extraction
            keywords = extract_keywords(text)
            dashboard_data['global_topics'].update(keywords)

            # 7. Aggregate into Timeline Buckets
            if bucket not in dashboard_data['timeline']:
                dashboard_data['timeline'][bucket] = {
                    "count": 0,
                    "sentiment_sum": 0,
                    "rhetoric_sum": {k: 0 for k in rhetoric},
                    "top_comment": {"text": "", "votes": -1}
                }

            # Update Bucket
            b_data = dashboard_data['timeline'][bucket]
            b_data['count'] += 1
            b_data['sentiment_sum'] += compound_score
            for k, v in rhetoric.items():
                b_data['rhetoric_sum'][k] += v

            # Track top comment for this bucket
            if votes > b_data['top_comment']['votes']:
                b_data['top_comment'] = {"author": author, "text": text, "votes": votes}

        except json.JSONDecodeError:
            continue

# --- POST PROCESSING & FORMATTING ---
final_output = {
    "timeline_points": [],
    "top_keywords": dashboard_data['global_topics'].most_common(20),
    "fact_check_feed": sorted(dashboard_data['fact_checks'], key=lambda x: x['votes'], reverse=True)[:10],
    "confusion_feed": sorted(dashboard_data['confusion_questions'], key=lambda x: x['votes'], reverse=True)[:10]
}

# Average out the bucket data
for bucket_time, data in sorted(dashboard_data['timeline'].items()):
    count = data['count']
    if count == 0: continue

    avg_rhetoric = {k: round(v / count, 2) for k, v in data['rhetoric_sum'].items()}

    final_output['timeline_points'].append({
        "seconds": bucket_time,
        "display_time": f"{bucket_time // 60}:{bucket_time % 60:02d}",
        "volume": count,
        "avg_sentiment": round(data['sentiment_sum'] / count, 2),
        "rhetorical_profile": avg_rhetoric,
        "top_comment": data['top_comment']
    })

# Save to file
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(final_output, f, indent=4)

print(f"Analysis complete! Data saved to {OUTPUT_FILE}")
print(f"Found {len(final_output['fact_check_feed'])} potential fact checks.")
print(f"Generated {len(final_output['timeline_points'])} timeline points.")
