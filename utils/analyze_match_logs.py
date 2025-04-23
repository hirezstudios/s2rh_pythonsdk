#!/usr/bin/env python3
"""
Script to analyze and visualize data from processed combat and chat logs.

This script combines data from combat logs and chat logs to provide insights
and visualizations for match analysis.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
from pathlib import Path
from datetime import datetime

def load_data(combat_csv, chat_csv):
    """Load data from combat and chat log CSV files."""
    combat_df = None
    chat_df = None
    
    # Load combat log data if file exists
    if os.path.exists(combat_csv):
        try:
            combat_df = pd.read_csv(combat_csv)
            print(f"Loaded {len(combat_df)} combat events from {combat_csv}")
        except Exception as e:
            print(f"Error loading combat log data: {str(e)}")
    else:
        print(f"Combat log CSV file not found: {combat_csv}")
    
    # Load chat log data if file exists
    if os.path.exists(chat_csv):
        try:
            chat_df = pd.read_csv(chat_csv)
            print(f"Loaded {len(chat_df)} chat messages from {chat_csv}")
        except Exception as e:
            print(f"Error loading chat log data: {str(e)}")
    else:
        print(f"Chat log CSV file not found: {chat_csv}")
    
    return combat_df, chat_df

def analyze_combat_data(combat_df, output_dir):
    """Analyze combat log data and generate visualizations."""
    if combat_df is None or len(combat_df) == 0:
        print("No combat data to analyze")
        return
    
    print("\n--- Combat Log Analysis ---")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Basic statistics
    print(f"Total combat events: {len(combat_df)}")
    
    # Count event types
    if 'event_type' in combat_df.columns:
        event_counts = combat_df['event_type'].value_counts()
        print("\nEvent type distribution:")
        for event_type, count in event_counts.items():
            print(f"  {event_type}: {count}")
        
        # Plot event type distribution
        plt.figure(figsize=(12, 6))
        sns.barplot(x=event_counts.index, y=event_counts.values)
        plt.title('Combat Event Type Distribution')
        plt.xlabel('Event Type')
        plt.ylabel('Count')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'event_type_distribution.png'))
        plt.close()
    
    # Analyze damage events if they exist
    if 'event_type' in combat_df.columns and 'damage' in combat_df.columns:
        damage_events = combat_df[combat_df['event_type'] == 'Damage']
        
        if len(damage_events) > 0:
            print(f"\nTotal damage events: {len(damage_events)}")
            
            # Damage statistics
            print(f"Total damage dealt: {damage_events['damage'].sum()}")
            print(f"Average damage per event: {damage_events['damage'].mean():.2f}")
            print(f"Max damage in a single event: {damage_events['damage'].max()}")
            
            # Plot damage distribution
            plt.figure(figsize=(10, 6))
            sns.histplot(damage_events['damage'], bins=20, kde=True)
            plt.title('Damage Distribution')
            plt.xlabel('Damage Amount')
            plt.ylabel('Frequency')
            plt.savefig(os.path.join(output_dir, 'damage_distribution.png'))
            plt.close()
            
            # Top damaging events
            if 'source_name' in damage_events.columns and 'target_name' in damage_events.columns:
                # Group by source and target, sum damage
                source_target_damage = damage_events.groupby(['source_name', 'target_name'])['damage'].sum().reset_index()
                source_target_damage = source_target_damage.sort_values('damage', ascending=False)
                
                print("\nTop 10 source-target damage combinations:")
                for _, row in source_target_damage.head(10).iterrows():
                    print(f"  {row['source_name']} → {row['target_name']}: {row['damage']:.2f}")
                
                # Damage by source
                source_damage = damage_events.groupby('source_name')['damage'].sum().sort_values(ascending=False)
                
                plt.figure(figsize=(12, 6))
                sns.barplot(x=source_damage.index[:10], y=source_damage.values[:10])
                plt.title('Top 10 Damage Sources')
                plt.xlabel('Source')
                plt.ylabel('Total Damage')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                plt.savefig(os.path.join(output_dir, 'top_damage_sources.png'))
                plt.close()
    
    # Time-based analysis if timestamp column exists
    if 'timestamp' in combat_df.columns:
        try:
            # Convert timestamp to datetime
            combat_df['timestamp'] = pd.to_datetime(combat_df['timestamp'])
            
            # Group events by minute
            combat_df['minute'] = combat_df['timestamp'].dt.floor('1min')
            events_by_minute = combat_df.groupby('minute').size()
            
            # Plot events over time
            plt.figure(figsize=(14, 6))
            events_by_minute.plot()
            plt.title('Combat Events Over Time')
            plt.xlabel('Time')
            plt.ylabel('Number of Events')
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'events_over_time.png'))
            plt.close()
            
            # If damage events exist, plot damage over time
            if 'event_type' in combat_df.columns and 'damage' in combat_df.columns:
                damage_over_time = combat_df[combat_df['event_type'] == 'Damage'].groupby('minute')['damage'].sum()
                
                plt.figure(figsize=(14, 6))
                damage_over_time.plot()
                plt.title('Damage Dealt Over Time')
                plt.xlabel('Time')
                plt.ylabel('Total Damage')
                plt.tight_layout()
                plt.savefig(os.path.join(output_dir, 'damage_over_time.png'))
                plt.close()
        except Exception as e:
            print(f"Error in time-based analysis: {str(e)}")
    
    print(f"\nCombat analysis visualizations saved to {output_dir}")

def analyze_chat_data(chat_df, output_dir):
    """Analyze chat log data and generate visualizations."""
    if chat_df is None or len(chat_df) == 0:
        print("No chat data to analyze")
        return
    
    print("\n--- Chat Log Analysis ---")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Basic statistics
    print(f"Total chat messages: {len(chat_df)}")
    
    # Analyze moderation results
    if 'mod_result' in chat_df.columns:
        mod_result_counts = chat_df['mod_result'].value_counts()
        print("\nModeration result distribution:")
        for result, count in mod_result_counts.items():
            percentage = (count / len(chat_df)) * 100
            print(f"  {result}: {count} ({percentage:.1f}%)")
        
        # Plot moderation result distribution
        plt.figure(figsize=(10, 6))
        sns.barplot(x=mod_result_counts.index, y=mod_result_counts.values)
        plt.title('Chat Moderation Result Distribution')
        plt.xlabel('Moderation Result')
        plt.ylabel('Count')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'moderation_results.png'))
        plt.close()
    
    # Analyze message length
    chat_df['message_length'] = chat_df['message'].apply(len)
    
    print(f"\nAverage message length: {chat_df['message_length'].mean():.2f} characters")
    print(f"Longest message: {chat_df['message_length'].max()} characters")
    
    # Plot message length distribution
    plt.figure(figsize=(10, 6))
    sns.histplot(chat_df['message_length'], bins=20, kde=True)
    plt.title('Message Length Distribution')
    plt.xlabel('Message Length (characters)')
    plt.ylabel('Frequency')
    plt.savefig(os.path.join(output_dir, 'message_length_distribution.png'))
    plt.close()
    
    # Analyze messages by team
    if 'team_id' in chat_df.columns:
        team_message_counts = chat_df['team_id'].value_counts()
        
        print("\nMessages by team:")
        for team_id, count in team_message_counts.items():
            percentage = (count / len(chat_df)) * 100
            print(f"  Team {team_id}: {count} ({percentage:.1f}%)")
        
        # Plot messages by team
        plt.figure(figsize=(10, 6))
        sns.barplot(x=team_message_counts.index, y=team_message_counts.values)
        plt.title('Messages by Team')
        plt.xlabel('Team ID')
        plt.ylabel('Number of Messages')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'messages_by_team.png'))
        plt.close()
    
    # Analyze message moderation scores
    score_columns = ['hate_score', 'selfharm_score', 'sexual_score', 'violence_score']
    if all(col in chat_df.columns for col in score_columns):
        # Calculate average scores
        print("\nAverage moderation scores:")
        for col in score_columns:
            print(f"  {col}: {chat_df[col].mean():.4f}")
        
        # Create score distribution plot
        plt.figure(figsize=(12, 8))
        for i, col in enumerate(score_columns, 1):
            plt.subplot(2, 2, i)
            sns.histplot(chat_df[col], bins=20, kde=True)
            plt.title(f'{col.replace("_score", "").capitalize()} Score Distribution')
            plt.xlabel('Score')
            plt.ylabel('Frequency')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'moderation_score_distributions.png'))
        plt.close()
    
    print(f"\nChat analysis visualizations saved to {output_dir}")

def combined_analysis(combat_df, chat_df, output_dir):
    """Perform combined analysis on combat and chat data."""
    if combat_df is None or chat_df is None:
        print("\nCannot perform combined analysis without both combat and chat data")
        return
    
    print("\n--- Combined Analysis ---")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if we have matching match_ids in both datasets
    if 'match_id' in combat_df.columns and 'match_id' in chat_df.columns:
        combat_matches = set(combat_df['match_id'].unique())
        chat_matches = set(chat_df['match_id'].unique())
        common_matches = combat_matches.intersection(chat_matches)
        
        print(f"Matches in combat data: {len(combat_matches)}")
        print(f"Matches in chat data: {len(chat_matches)}")
        print(f"Common matches: {len(common_matches)}")
        
        if len(common_matches) == 0:
            print("No common matches found, skipping combined analysis")
            return
        
        # Filter data to only include common matches
        filtered_combat = combat_df[combat_df['match_id'].isin(common_matches)]
        filtered_chat = chat_df[chat_df['match_id'].isin(common_matches)]
        
        # Analyze message activity relative to combat events
        if 'timestamp' in filtered_combat.columns and 'line_index' in filtered_chat.columns:
            try:
                # Convert timestamps
                filtered_combat['timestamp'] = pd.to_datetime(filtered_combat['timestamp'])
                
                # Group by match and minute
                filtered_combat['minute'] = filtered_combat['timestamp'].dt.floor('1min')
                combat_by_minute = filtered_combat.groupby(['match_id', 'minute']).size().reset_index(name='combat_events')
                
                # For chat data, we'll use line_index as a proxy for temporal ordering
                chat_by_match = filtered_chat.groupby('match_id').size().reset_index(name='chat_messages')
                
                # Join data
                combined_data = pd.merge(combat_by_minute, chat_by_match, on='match_id', how='left')
                
                # Create scatter plot of combat events vs chat messages by match
                plt.figure(figsize=(10, 8))
                plt.scatter(combined_data['combat_events'], combined_data['chat_messages'])
                plt.title('Combat Events vs Chat Messages by Match')
                plt.xlabel('Number of Combat Events')
                plt.ylabel('Number of Chat Messages')
                plt.savefig(os.path.join(output_dir, 'combat_vs_chat.png'))
                plt.close()
            except Exception as e:
                print(f"Error in combined temporal analysis: {str(e)}")
    
    # Create a summary report file
    report_path = os.path.join(output_dir, 'analysis_summary.txt')
    with open(report_path, 'w') as f:
        f.write("MATCH LOGS ANALYSIS SUMMARY\n")
        f.write("==========================\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("Combat Log Statistics:\n")
        f.write(f"- Total combat events: {len(combat_df) if combat_df is not None else 0}\n")
        if combat_df is not None and 'event_type' in combat_df.columns:
            event_counts = combat_df['event_type'].value_counts()
            f.write("- Event types:\n")
            for event_type, count in event_counts.items():
                f.write(f"  * {event_type}: {count}\n")
        
        f.write("\nChat Log Statistics:\n")
        f.write(f"- Total chat messages: {len(chat_df) if chat_df is not None else 0}\n")
        if chat_df is not None and 'mod_result' in chat_df.columns:
            mod_result_counts = chat_df['mod_result'].value_counts()
            f.write("- Moderation results:\n")
            for result, count in mod_result_counts.items():
                percentage = (count / len(chat_df)) * 100
                f.write(f"  * {result}: {count} ({percentage:.1f}%)\n")
        
        f.write("\nAnalysis Files:\n")
        for file in os.listdir(output_dir):
            if file.endswith('.png'):
                f.write(f"- {file}\n")
    
    print(f"\nCombined analysis visualizations and summary saved to {output_dir}")

def main():
    """Main function to process command line arguments and run analysis."""
    parser = argparse.ArgumentParser(description="Analyze combat and chat log data")
    parser.add_argument(
        "--combat-csv", "-c", 
        default="combat_logs.csv", 
        help="Combat log CSV file path (default: combat_logs.csv)"
    )
    parser.add_argument(
        "--chat-csv", "-m", 
        default="chat_logs.csv", 
        help="Chat log CSV file path (default: chat_logs.csv)"
    )
    parser.add_argument(
        "--output-dir", "-o", 
        default="analysis_results", 
        help="Output directory for analysis results (default: analysis_results)"
    )
    
    args = parser.parse_args()
    
    # Load data
    combat_df, chat_df = load_data(args.combat_csv, args.chat_csv)
    
    # Perform analysis
    if combat_df is not None:
        analyze_combat_data(combat_df, args.output_dir)
    
    if chat_df is not None:
        analyze_chat_data(chat_df, args.output_dir)
    
    if combat_df is not None and chat_df is not None:
        combined_analysis(combat_df, chat_df, args.output_dir)
    
    print(f"\nAnalysis complete. Results saved to {args.output_dir}")

if __name__ == "__main__":
    main() 