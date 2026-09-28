from filer_names.dotcom_bubble import generate_dotcom_bubble_indicators
from filer_names.name_changes import generate_name_changes_indicators
from filer_metadata.summary import aggregate_filer_metadata
from mentions.mentions import create_indicator
import shutil
import os
import urllib.request
import json
import re
from collections import defaultdict

# Define the category map once at the module level
CATEGORY_MAP = {
    'dei': 'Governance',
    'esg': 'Governance',
    'tariffs': 'Trade',
    'layoffs': 'Employment',
    'outsourcing': 'Market Dynamics',
    'consumer-confidence': 'Consumer Sentiment',
    'supplier-concentration': 'Market Dynamics',
    'war': 'War',
    'terrorism': 'Terrorism',
    'space' : "Technology",
    'nuclear' : "Technology",
    "sovereign-crisis" : "International",
    "political-stability" : "International",
    'ipo': 'Corporate Finance',
    'explosive-materials' : "Resources",
    'metals' : 'Resources',
    'semiconductor-materials' : 'Resources',
    'propellant-components' : 'Resources',
    'raw-materials' : 'Resources',
    'electronic-components' : 'Resources',
    'chemicals' : 'Resources',
    'supply-chain' : 'Trade',
    'military-equipment' : 'War',
    "llm" : "Technology",
    "health" : "Health",
    "pandemic" : "Health",
    "health-research" : "Health",
    "bitcoin" : "Blockchain",
    "ethereum" : "Blockchain",
    "stablecoin" : "Blockchain",
    "defi" : "Blockchain",
    "nft" : "Blockchain"
    }

def get_prefix(mention_key):
    """Extract the prefix from a mention key (everything before the underscore)."""
    match = re.match(r'([^_]+)_', mention_key)
    if match:
        return match.group(1)
    return mention_key  # If no underscore, use the whole key

def map_prefix_to_category(prefix):
    """Map prefix to a category."""
    return CATEGORY_MAP.get(prefix, 'Other')

def generate_indicators_json():
    """
    Generate a JSON file mapping categories to their indicators.
    Saves to indicators/indicators.json
    """
    # Initialize the structure with all categories having empty arrays
    categories = defaultdict(list)
    
    # Add "Other" category
    categories["Other"] = []
    
    # Populate based on the indicators we've created
    # For each indicator in our system, add it to the appropriate category
    for prefix, category in CATEGORY_MAP.items():
        categories[category].append(prefix)
    
    # Create the final structure
    indicators_json = {
        "categories": dict(categories)
    }
    
    # Ensure the indicators directory exists
    os.makedirs('indicators', exist_ok=True)
    
    # Write the JSON file
    with open('indicators/indicators.json', 'w') as f:
        json.dump(indicators_json, f, indent=2)
    
    print("Generated indicators.json successfully!")


if __name__ == "__main__":


    # Delete indicators/ folder for fresh start
    if os.path.exists('indicators'):
        shutil.rmtree('indicators')

    # Load the data from GitHub
    data_json = urllib.request.urlopen("https://raw.githubusercontent.com/john-friedman/datamule-data/refs/heads/scripts/data.json").read()

    
    data_dict = json.loads(data_json)
    mentions_data = data_dict.get('mentions', {})

    # Group mentions by their prefix
    grouped_mentions = defaultdict(list)
    for mention_key, mention_data in mentions_data.items():
        prefix = get_prefix(mention_key)
        grouped_mentions[prefix].append((mention_key, mention_data))
    
    # Create indicators for each group
    for prefix, mentions in grouped_mentions.items():
        # Get category and indicator name
        category = map_prefix_to_category(prefix)
        indicator_name = prefix
        print(f"Creating indicator: {category}/{indicator_name}")
        # Collect component URLs and query lists
        components = []
        query_list = []
        
        # Check if all mentions have the same submission and document type
        submission_types = set()
        
        for mention_key, mention_data in mentions:
            # Get submission type and document type
            submission_type = mention_data['submission_type'][0]
            document_type = mention_data['document_type'][0]
            submission_types.add(submission_type)
            
            # Build URL
            url = f"https://github.com/john-friedman/datamule-data/raw/refs/heads/master/data/mentions/{submission_type}/{document_type}/{mention_key}.csv.gz"
            components.append(url)
            
            # Add query list
            query_list.append(mention_data['query'])
        
        # Determine interval and period based on submission type
        if '10-K' in submission_types:
            interval = 'YE'
            period = 365
        elif '8-K' in submission_types:
            interval = 'ME'
            period = 30
        elif "18-K" in submission_types:
            interval = 'YE'
            period = 365
        elif '20-F' in submission_types:
            interval = 'YE'
            period = 365
        elif '6-K' in submission_types:
            interval = 'ME'
            period = 30
        elif 'S-1' in submission_types:
            interval = 'YE'
            period = 365
        elif 'F-1' in submission_types:
            interval = 'YE'
            period = 365
        else:
            interval = 'QE'
            period = 90
        
        # Create the indicator
        create_indicator(
            format='format1',
            category=category,
            indicator=indicator_name,
            components=components,
            interval=interval,
            period=period,
            query_list=query_list
        )
        
        print(f"Created indicator: {category}/{indicator_name}")
        print(f"  - Components: {len(components)}")
        print(f"  - Interval: {interval}, Period: {period}")
    
    generate_dotcom_bubble_indicators(output_dir="data/filer_names")
    generate_name_changes_indicators(output_dir="data/filer_names")
    
    # Generate the indicators.json file
    generate_indicators_json()

    # old code
    aggregate_filer_metadata("data/filer_metadata") 
    
    print("All indicators created successfully!")