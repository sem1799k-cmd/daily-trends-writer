import os
import urllib.request
import xml.etree.ElementTree as ET
from google import genai

# Pull the API key securely from GitHub Secrets
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is missing!")

# Initialize Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY)


def fetch_top_trend(geo="US"):
    """Fetch today's #1 top trending search from Google Trends RSS."""
    rss_url = f"https://trends.google.com/trending/rss?geo={geo}"
    headers = {"User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request(rss_url, headers=headers)

    xml_data = urllib.request.urlopen(req).read()
    root = ET.fromstring(xml_data)
    ns = {"ht": "https://trends.google.com/trending/rss"}

    item = root.find("./channel/item")
    if item is not None:
        title = (
            item.find("title").text if item.find("title") is not None else "N/A"
        )
        approx_traffic = item.find("ht:approx_traffic", ns)
        search_vol = (
            approx_traffic.text if approx_traffic is not None else "N/A"
        )
        snippet = (
            item.find("description").text
            if item.find("description") is not None
            else ""
        )
        return {"keyword": title, "volume": search_vol, "context": snippet}
    return None


def generate_article_with_gemini(trend):
    """Pass extracted trend keywords and context to Gemini to write an article."""
    prompt = f"""
    You are an expert news and blog content creator.
    
    Today's top trending search keyword is: "{trend['keyword']}"
    Estimated Search Volume Today: {trend['volume']}
    Context/News Snippet: {trend['context']}

    Please write a comprehensive, engaging, and SEO-friendly article based on this trending event.
    
    Structure the article as follows:
    1. **Catchy Title** (incorporating the keyword naturally)
    2. **Introduction**: What happened and why is this currently trending?
    3. **Key Takeaways / Main Details**: Break down the core facts or event updates.
    4. **Why It Matters / Public Reaction**: Brief analysis of why people are searching for this.
    5. **Conclusion**: Summary statement.
    
    Keep the tone informative, objective, and well-formatted using Markdown headings and bullet points.
    """

    print(f"🤖 Sending '{trend['keyword']}' to Gemini for drafting...")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text


if __name__ == "__main__":
    print("🔍 Fetching today's top trending keyword from Google Trends...")
    top_trend = fetch_top_trend(geo="US")

    if top_trend:
        print(f"✅ Found Top Trend: '{top_trend['keyword']}'\n")
        article_markdown = generate_article_with_gemini(top_trend)

        # Sanitize filename
        safe_title = "".join(
            c
            for c in top_trend["keyword"]
            if c.isalnum() or c in (" ", "-", "_")
        ).strip()
        filename = f"article_{safe_title.replace(' ', '_')}.md"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(article_markdown)

        print(f"🎉 Article successfully saved to '{filename}'!")
    else:
        print("❌ Could not fetch trending topics.")
