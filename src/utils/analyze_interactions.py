import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter

def analyze_interactions():
    
    # Get the project root directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    db_path = os.path.join(project_root, 'user_interactions.db')
    
    # Connect to the database
    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)    
    
    # Read data from the interactions table
    try:
        df = pd.read_sql_query("SELECT * FROM interactions", conn)
        conn.close()
    except Exception as e:
        print(f"Error reading data from the database: {e}")
        return
    
        # Analyze and visualize the data
    if not df.empty:
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
        daily_counts.plot(kind='line', marker='o', color='skyblue')
        plt.title('Daily Interactions')
        plt.xlabel('Date')
        plt.ylabel('Number of Interactions')
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save the plot
        plot_path = os.path.join(project_root, 'daily_interactions.png')
        plt.savefig(plot_path)
        plt.show()
        print(f"Plot saved at: {plot_path}")

        # Word frequency in user inputs
        words = ' '.join(df['user_input']).lower().split()
        word_freq = Counter(words)
        print("\nTop 10 most common words in user queries:")
        print(pd.DataFrame(word_freq.most_common(10), columns=['Word', 'Frequency']))
    else:
        print("No interactions found in the database.")
        
    conn.close()

if __name__ == "__main__":
    analyze_interactions()