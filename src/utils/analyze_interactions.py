import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def analyze_interactions():
    conn = sqlite3.connect('user_interactions.db')
    
    # Load data into a pandas DataFrame
    df = pd.read_sql_query("SELECT * FROM interactions", conn)
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Basic statistics
    print(f"Total interactions: {len(df)}")
    print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    # Most common user queries
    print("\nTop 5 most common user queries:")
    print(df['user_input'].value_counts().head())
    
    # Interactions over time
    df['date'] = df['timestamp'].dt.date
    daily_counts = df.groupby('date').size()
    
    plt.figure(figsize=(12, 6))
    daily_counts.plot(kind='line')
    plt.title('Daily Interactions')
    plt.xlabel('Date')
    plt.ylabel('Number of Interactions')
    plt.savefig('daily_interactions.png')
    plt.close()
    
    # Word frequency in user inputs
    from collections import Counter
    words = ' '.join(df['user_input']).lower().split()
    word_freq = Counter(words)
    print("\nTop 10 most common words in user queries:")
    print(pd.DataFrame(word_freq.most_common(10), columns=['Word', 'Frequency']))
    
    conn.close()

if __name__ == "__main__":
    analyze_interactions()