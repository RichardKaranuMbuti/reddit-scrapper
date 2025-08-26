#!/usr/bin/env python3
# streamlit_app.py
"""Streamlit UI for filtering and viewing analyzed job postings"""

import streamlit as st
import asyncio
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any
import json

from database import JobDatabase
from config import DEFAULT_TIME_FILTERS, DATABASE_FILE

# Set page configuration
st.set_page_config(
    page_title="Reddit Job Scraper Dashboard",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
@st.cache_resource
def get_database():
    """Get database instance"""
    return JobDatabase(DATABASE_FILE)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_database_stats():
    """Get database statistics"""
    db = get_database()
    return asyncio.run(db.get_stats())

@st.cache_data(ttl=60)  # Cache for 1 minute
def get_analyzed_jobs(hours_back: int, worth_checking_only: bool = False):
    """Get analyzed jobs from database"""
    db = get_database()
    return asyncio.run(db.get_analyzed_jobs(hours_back, worth_checking_only))

def format_job_card(job: Dict[str, Any]) -> str:
    """Format a job posting as an HTML card"""
    # Determine card color based on worth_checking and confidence
    if job['worth_checking']:
        confidence = job['confidence_score']
        if confidence >= 80:
            card_color = "#d4edda"  # Light green
            border_color = "#28a745"  # Green
        elif confidence >= 60:
            card_color = "#fff3cd"  # Light yellow
            border_color = "#ffc107"  # Yellow
        else:
            card_color = "#f8d7da"  # Light red
            border_color = "#dc3545"  # Red
    else:
        card_color = "#f8f9fa"  # Light gray
        border_color = "#6c757d"  # Gray
    
    # Format highlights and red flags
    highlights = job.get('key_highlights', [])
    red_flags = job.get('red_flags', [])
    
    highlights_html = ""
    if highlights:
        highlights_html = "<br>".join([f"✅ {h}" for h in highlights[:3]])
    
    red_flags_html = ""
    if red_flags:
        red_flags_html = "<br>".join([f"❌ {f.replace('_', ' ').title()}" for f in red_flags[:3]])
    
    # Truncate description
    description = job.get('description', 'No description available')
    if len(description) > 200:
        description = description[:200] + "..."
    
    card_html = f"""
    <div style="
        border: 2px solid {border_color};
        background-color: {card_color};
        padding: 15px;
        margin: 10px 0;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">
        <h3 style="margin-top: 0; color: #333;">
            <a href="{job['url']}" target="_blank" style="text-decoration: none; color: #007bff;">
                {job['title']}
            </a>
        </h3>
        
        <div style="display: flex; gap: 20px; margin-bottom: 10px;">
            <span><strong>📍 Subreddit:</strong> {job['subreddit']}</span>
            <span><strong>⏰ Posted:</strong> {job['time_posted']}</span>
            <span><strong>🎯 Confidence:</strong> {job['confidence_score']:.0f}%</span>
        </div>
        
        <div style="margin-bottom: 10px;">
            <strong>💼 Job Type:</strong> {job['job_type'].replace('_', ' ').title()}&nbsp;&nbsp;
            <strong>💰 Compensation:</strong> {'Yes' if job['compensation_mentioned'] else 'No'}&nbsp;&nbsp;
            <strong>🏠 Remote:</strong> {'Yes' if job['remote_friendly'] else 'No'}&nbsp;&nbsp;
            <strong>📈 Level:</strong> {job['experience_level'].title()}
        </div>
        
        <p style="color: #666; margin-bottom: 10px;"><strong>Description:</strong> {description}</p>
        
        {f'<div style="margin-bottom: 10px;"><strong style="color: green;">Highlights:</strong><br>{highlights_html}</div>' if highlights_html else ''}
        
        {f'<div style="margin-bottom: 10px;"><strong style="color: red;">Red Flags:</strong><br>{red_flags_html}</div>' if red_flags_html else ''}
        
        <div style="margin-top: 15px; padding: 10px; background-color: rgba(0,0,0,0.05); border-radius: 5px;">
            <strong>🤖 AI Recommendation:</strong> {job['recommendation']}
        </div>
        
        <div style="margin-top: 10px; font-size: 0.8em; color: #888;">
            <strong>Analyzed:</strong> {pd.to_datetime(job['analyzed_at']).strftime('%Y-%m-%d %H:%M')}
        </div>
    </div>
    """
    return card_html

def main():
    st.title("💼 Reddit Job Scraper Dashboard")
    st.markdown("Filter and view AI-analyzed job postings from Reddit")
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Bookmarks section
    if 'bookmarked_jobs' not in st.session_state:
        st.session_state.bookmarked_jobs = set()
    
    if st.session_state.bookmarked_jobs:
        st.sidebar.subheader("🔖 Bookmarks")
        bookmark_count = len(st.session_state.bookmarked_jobs)
        st.sidebar.write(f"You have {bookmark_count} bookmarked job(s)")
        
        if st.sidebar.button("📋 View Bookmarks"):
            # Filter to show only bookmarked jobs
            st.session_state.show_bookmarks_only = True
            st.experimental_rerun()
        
        if st.sidebar.button("🗑️ Clear All Bookmarks"):
            st.session_state.bookmarked_jobs.clear()
            st.sidebar.success("All bookmarks cleared!")
            st.experimental_rerun()
    
    # Reset bookmarks filter
    if hasattr(st.session_state, 'show_bookmarks_only') and st.session_state.show_bookmarks_only:
        if st.sidebar.button("🔄 Show All Jobs"):
            st.session_state.show_bookmarks_only = False
            st.experimental_rerun()
        st.sidebar.info("Currently showing bookmarked jobs only")
    
    st.sidebar.markdown("---")
    
    # Time filter
    time_options = {name: hours for name, hours in DEFAULT_TIME_FILTERS}
    selected_time = st.sidebar.selectbox(
        "📅 Time Range",
        options=list(time_options.keys()),
        index=2  # Default to "Last 24 hours"
    )
    hours_back = time_options[selected_time]
    
    # Worth checking filter
    worth_filter = st.sidebar.radio(
        "🎯 Job Quality",
        options=["All Jobs", "Worth Checking Only", "Not Worth Checking"],
        index=1  # Default to "Worth Checking Only"
    )
    
    # Additional filters
    st.sidebar.subheader("🔧 Additional Filters")
    
    min_confidence = st.sidebar.slider(
        "Minimum Confidence Score",
        min_value=0,
        max_value=100,
        value=50,
        step=5
    )
    
    show_remote_only = st.sidebar.checkbox("🏠 Remote Friendly Only", value=False)
    show_compensation_only = st.sidebar.checkbox("💰 Compensation Mentioned Only", value=False)
    
    # Experience level filter
    experience_levels = ["All", "entry", "mid", "senior", "lead", "unspecified"]
    selected_experience = st.sidebar.selectbox(
        "📈 Experience Level",
        options=experience_levels,
        index=0
    )
    
    # Job type filter
    job_types = ["All", "full_time", "part_time", "contract", "freelance", "internship", "unspecified"]
    selected_job_type = st.sidebar.selectbox(
        "💼 Job Type",
        options=job_types,
        index=0
    )
    
    # Main content
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        # Get database stats
        stats = get_database_stats()
        
        with col1:
            st.metric("📊 Total Jobs", stats['total_jobs'])
        with col2:
            st.metric("🤖 Analyzed", stats['analyzed_jobs'])
        with col3:
            st.metric("✅ Worth Checking", stats['worth_checking'])
        with col4:
            st.metric("📅 Last 24h", stats['jobs_last_24h'])
        
        # Get filtered jobs
        worth_checking_only = worth_filter == "Worth Checking Only"
        if worth_filter == "Not Worth Checking":
            # We'll filter this after getting the data
            worth_checking_only = False
        
        jobs = get_analyzed_jobs(hours_back, worth_checking_only)
        
        if not jobs:
            st.warning(f"No analyzed jobs found in the selected time range ({selected_time})")
            st.info("Make sure the scraper is running and has analyzed some jobs.")
            return
        
        # Convert to DataFrame for easier filtering
        df = pd.DataFrame(jobs)
        
        # Apply bookmarks filter if active
        if hasattr(st.session_state, 'show_bookmarks_only') and st.session_state.show_bookmarks_only:
            if st.session_state.bookmarked_jobs:
                df = df[df['url'].isin(st.session_state.bookmarked_jobs)]
                if len(df) == 0:
                    st.warning("No bookmarked jobs found in the current time range.")
                    st.info("Try expanding your time range or bookmark some jobs first.")
                    return
            else:
                st.warning("No jobs are bookmarked yet.")
                return
        
        # Apply additional filters
        if worth_filter == "Not Worth Checking":
            df = df[df['worth_checking'] == False]
        
        df = df[df['confidence_score'] >= min_confidence]
        
        if show_remote_only:
            df = df[df['remote_friendly'] == True]
        
        if show_compensation_only:
            df = df[df['compensation_mentioned'] == True]
        
        if selected_experience != "All":
            df = df[df['experience_level'] == selected_experience]
        
        if selected_job_type != "All":
            df = df[df['job_type'] == selected_job_type]
        
        # Display results summary with dynamic updates
        filtered_count = len(df)
        if hasattr(st.session_state, 'show_bookmarks_only') and st.session_state.show_bookmarks_only:
            st.subheader(f"🔖 Bookmarked Jobs ({filtered_count} jobs)")
        else:
            st.subheader(f"📋 Results ({filtered_count} jobs)")
        
        if len(df) == 0:
            if hasattr(st.session_state, 'show_bookmarks_only') and st.session_state.show_bookmarks_only:
                st.warning("No bookmarked jobs match your current filters.")
            else:
                st.warning("No jobs match your current filters. Try adjusting the criteria.")
            return
        
        # Summary metrics for filtered results
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            avg_confidence = df['confidence_score'].mean()
            st.metric("🎯 Avg Confidence", f"{avg_confidence:.1f}%")
        with col2:
            remote_count = df['remote_friendly'].sum()
            st.metric("🏠 Remote Jobs", f"{remote_count}/{len(df)}")
        with col3:
            compensation_count = df['compensation_mentioned'].sum()
            st.metric("💰 With Compensation", f"{compensation_count}/{len(df)}")
        with col4:
            worth_count = df['worth_checking'].sum()
            st.metric("✅ Worth Checking", f"{worth_count}/{len(df)}")
        
        # Visualization tabs
        tab1, tab2, tab3 = st.tabs(["📊 Analytics", "📋 Job List", "📈 Trends"])
        
        with tab1:
            # Analytics charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Confidence score distribution
                fig_confidence = px.histogram(
                    df, 
                    x='confidence_score',
                    nbins=20,
                    title="Confidence Score Distribution",
                    color_discrete_sequence=['#1f77b4']
                )
                fig_confidence.update_layout(
                    xaxis_title="Confidence Score",
                    yaxis_title="Number of Jobs"
                )
                st.plotly_chart(fig_confidence, use_container_width=True)
            
            with col2:
                # Job type distribution
                job_type_counts = df['job_type'].value_counts()
                fig_job_type = px.pie(
                    values=job_type_counts.values,
                    names=[jt.replace('_', ' ').title() for jt in job_type_counts.index],
                    title="Job Type Distribution"
                )
                st.plotly_chart(fig_job_type, use_container_width=True)
            
            col3, col4 = st.columns(2)
            
            with col3:
                # Subreddit distribution
                subreddit_counts = df['subreddit'].value_counts().head(10)
                fig_subreddit = px.bar(
                    x=subreddit_counts.values,
                    y=subreddit_counts.index,
                    orientation='h',
                    title="Top Subreddits",
                    color_discrete_sequence=['#2ca02c']
                )
                fig_subreddit.update_layout(
                    xaxis_title="Number of Jobs",
                    yaxis_title="Subreddit"
                )
                st.plotly_chart(fig_subreddit, use_container_width=True)
            
            with col4:
                # Experience level distribution
                exp_counts = df['experience_level'].value_counts()
                fig_exp = px.bar(
                    x=exp_counts.index,
                    y=exp_counts.values,
                    title="Experience Level Distribution",
                    color_discrete_sequence=['#ff7f0e']
                )
                fig_exp.update_layout(
                    xaxis_title="Experience Level",
                    yaxis_title="Number of Jobs"
                )
                st.plotly_chart(fig_exp, use_container_width=True)
        
        with tab2:
            # Job list with search and sorting
            st.subheader("🔍 Search Jobs")
            
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                # Use preset search terms if available
                default_search = getattr(st.session_state, 'search_preset', "")
                search_term = st.text_input(
                    "Search in titles and descriptions", 
                    value=default_search,
                    help="Search for keywords in job titles and descriptions. Use spaces to search for multiple terms."
                )
            with col2:
                sort_by = st.selectbox(
                    "Sort by",
                    options=["analyzed_at", "confidence_score", "title"],
                    index=0
                )
            with col3:
                view_mode = st.selectbox(
                    "View Mode",
                    options=["List View", "Card Navigator"],
                    index=0
                )
            
            # Apply search filter with improved multi-term search
            filtered_df = df.copy()
            if search_term:
                # Split search terms and search for each
                search_terms = [term.strip().lower() for term in search_term.split() if term.strip()]
                if search_terms:
                    search_masks = []
                    for term in search_terms:
                        mask = (
                            filtered_df['title'].str.contains(term, case=False, na=False) |
                            filtered_df['description'].str.contains(term, case=False, na=False) |
                            filtered_df['subreddit'].str.contains(term, case=False, na=False) |
                            filtered_df['job_type'].str.contains(term, case=False, na=False) |
                            filtered_df['experience_level'].str.contains(term, case=False, na=False)
                        )
                        search_masks.append(mask)
                    
                    # Combine masks - job must match at least one search term
                    final_mask = search_masks[0]
                    for mask in search_masks[1:]:
                        final_mask = final_mask | mask
                    
                    filtered_df = filtered_df[final_mask]
            
            # Sort results
            if sort_by == "analyzed_at":
                filtered_df = filtered_df.sort_values('analyzed_at', ascending=False)
            elif sort_by == "confidence_score":
                filtered_df = filtered_df.sort_values('confidence_score', ascending=False)
            else:
                filtered_df = filtered_df.sort_values('title')
            
            st.write(f"Showing {len(filtered_df)} jobs")
            
            if view_mode == "Card Navigator":
                # Card Navigator Mode
                if len(filtered_df) > 0:
                    # Initialize session state for current job index
                    if 'current_job_index' not in st.session_state:
                        st.session_state.current_job_index = 0
                    
                    # Ensure index is within bounds
                    if st.session_state.current_job_index >= len(filtered_df):
                        st.session_state.current_job_index = 0
                    elif st.session_state.current_job_index < 0:
                        st.session_state.current_job_index = len(filtered_df) - 1
                    
                    # Navigation controls
                    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
                    
                    with col1:
                        if st.button("⏮️ First", key="first_job"):
                            st.session_state.current_job_index = 0
                            st.experimental_rerun()
                    
                    with col2:
                        if st.button("◀️ Previous", key="prev_job"):
                            if st.session_state.current_job_index > 0:
                                st.session_state.current_job_index -= 1
                                st.experimental_rerun()
                    
                    with col3:
                        st.write(f"**Job {st.session_state.current_job_index + 1} of {len(filtered_df)}**")
                        
                        # Jump to specific job
                        jump_to = st.number_input(
                            "Jump to job:",
                            min_value=1,
                            max_value=len(filtered_df),
                            value=st.session_state.current_job_index + 1,
                            key="jump_to_job"
                        )
                        if st.button("Go", key="jump_button"):
                            st.session_state.current_job_index = jump_to - 1
                            st.experimental_rerun()
                    
                    with col4:
                        if st.button("Next ▶️", key="next_job"):
                            if st.session_state.current_job_index < len(filtered_df) - 1:
                                st.session_state.current_job_index += 1
                                st.experimental_rerun()
                    
                    with col5:
                        if st.button("Last ⏭️", key="last_job"):
                            st.session_state.current_job_index = len(filtered_df) - 1
                            st.experimental_rerun()
                    
                    # Display current job in an enhanced card
                    current_job = filtered_df.iloc[st.session_state.current_job_index]
                    
                    # Enhanced job card with more details
                    st.markdown("---")
                    
                    # Job header
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"## 🔗 [{current_job['title']}]({current_job['url']})")
                    with col2:
                        # Quick actions
                        if st.button("🔗 Open Job", key="open_job"):
                            st.markdown(f"[Click here to open job]({current_job['url']})")
                        
                        # Bookmark functionality (stored in session state)
                        if 'bookmarked_jobs' not in st.session_state:
                            st.session_state.bookmarked_jobs = set()
                        
                        job_url = current_job['url']
                        is_bookmarked = job_url in st.session_state.bookmarked_jobs
                        bookmark_text = "🔖 Bookmarked" if is_bookmarked else "📌 Bookmark"
                        
                        if st.button(bookmark_text, key="bookmark_job"):
                            if is_bookmarked:
                                st.session_state.bookmarked_jobs.remove(job_url)
                                st.success("Removed from bookmarks!")
                            else:
                                st.session_state.bookmarked_jobs.add(job_url)
                                st.success("Added to bookmarks!")
                            st.experimental_rerun()
                    
                    # Job metadata
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("📍 Subreddit", current_job['subreddit'])
                    with col2:
                        st.metric("⏰ Posted", current_job['time_posted'])
                    with col3:
                        confidence_color = "normal"
                        if current_job['confidence_score'] >= 80:
                            confidence_color = "inverse"
                        st.metric("🎯 Confidence", f"{current_job['confidence_score']:.0f}%")
                    with col4:
                        worth_text = "✅ Yes" if current_job['worth_checking'] else "❌ No"
                        st.metric("💎 Worth Checking", worth_text)
                    
                    # Job details in expandable sections
                    with st.expander("📋 Job Details", expanded=True):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**💼 Job Information:**")
                            st.write(f"• **Type:** {current_job['job_type'].replace('_', ' ').title()}")
                            st.write(f"• **Experience:** {current_job['experience_level'].title()}")
                            st.write(f"• **Remote:** {'Yes' if current_job['remote_friendly'] else 'No'}")
                            st.write(f"• **Compensation:** {'Mentioned' if current_job['compensation_mentioned'] else 'Not mentioned'}")
                        
                        with col2:
                            st.write("**📊 AI Analysis:**")
                            st.write(f"• **Analyzed:** {pd.to_datetime(current_job['analyzed_at']).strftime('%Y-%m-%d %H:%M')}")
                            st.write(f"• **Model:** GPT-4o-mini")
                            st.write(f"• **Worth Checking:** {'Yes' if current_job['worth_checking'] else 'No'}")
                    
                    # Description
                    with st.expander("📄 Job Description", expanded=True):
                        description = current_job.get('description', 'No description available')
                        if description.strip():
                            st.markdown(f"```\n{description}\n```")
                        else:
                            st.info("No description available for this job posting.")
                    
                    # AI Analysis Results
                    with st.expander("🤖 AI Analysis Results", expanded=True):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Key highlights
                            highlights = current_job.get('key_highlights', [])
                            if highlights:
                                st.write("**✅ Key Highlights:**")
                                for highlight in highlights:
                                    st.write(f"• {highlight}")
                            else:
                                st.write("**✅ Key Highlights:** None identified")
                        
                        with col2:
                            # Red flags
                            red_flags = current_job.get('red_flags', [])
                            if red_flags:
                                st.write("**⚠️ Red Flags:**")
                                for flag in red_flags:
                                    st.write(f"• {flag.replace('_', ' ').title()}")
                            else:
                                st.write("**⚠️ Red Flags:** None identified")
                        
                        # AI Recommendation
                        st.write("**🎯 AI Recommendation:**")
                        recommendation = current_job.get('recommendation', 'No recommendation available')
                        st.info(recommendation)
                    
                    # Keyboard shortcuts info
                    with st.expander("⌨️ Keyboard Shortcuts"):
                        st.write("""
                        - **←/→ Arrow keys**: Navigate between jobs (when focused on navigation buttons)
                        - **Home/End**: Jump to first/last job
                        - **Space**: Open current job link
                        - **B**: Toggle bookmark (when button is focused)
                        """)
                    
                    # Navigation shortcuts with JavaScript (if supported)
                    st.markdown("""
                    <script>
                    document.addEventListener('keydown', function(event) {
                        if (event.target.tagName === 'INPUT') return;
                        
                        switch(event.key) {
                            case 'ArrowLeft':
                                document.querySelector('[data-testid="stButton"] button[key="prev_job"]')?.click();
                                break;
                            case 'ArrowRight':
                                document.querySelector('[data-testid="stButton"] button[key="next_job"]')?.click();
                                break;
                            case 'Home':
                                document.querySelector('[data-testid="stButton"] button[key="first_job"]')?.click();
                                break;
                            case 'End':
                                document.querySelector('[data-testid="stButton"] button[key="last_job"]')?.click();
                                break;
                        }
                    });
                    </script>
                    """, unsafe_allow_html=True)
                    
                else:
                    st.info("No jobs found matching your criteria.")
            
            else:
                # List View Mode (original)
                # Display job cards
                for _, job in filtered_df.iterrows():
                    st.markdown(format_job_card(job.to_dict()), unsafe_allow_html=True)
        
        with tab3:
            # Trends over time (if we have enough data)
            if len(df) > 5:
                df['analyzed_date'] = pd.to_datetime(df['analyzed_at']).dt.date
                daily_stats = df.groupby('analyzed_date').agg({
                    'worth_checking': ['count', 'sum'],
                    'confidence_score': 'mean'
                }).round(2)
                
                daily_stats.columns = ['Total_Jobs', 'Worth_Checking', 'Avg_Confidence']
                daily_stats = daily_stats.reset_index()
                
                if len(daily_stats) > 1:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Jobs over time
                        fig_timeline = px.line(
                            daily_stats,
                            x='analyzed_date',
                            y=['Total_Jobs', 'Worth_Checking'],
                            title="Jobs Analyzed Over Time",
                            labels={'value': 'Number of Jobs', 'analyzed_date': 'Date'}
                        )
                        st.plotly_chart(fig_timeline, use_container_width=True)
                    
                    with col2:
                        # Average confidence over time
                        fig_confidence_trend = px.line(
                            daily_stats,
                            x='analyzed_date',
                            y='Avg_Confidence',
                            title="Average Confidence Score Over Time",
                            labels={'Avg_Confidence': 'Average Confidence', 'analyzed_date': 'Date'},
                            color_discrete_sequence=['#d62728']
                        )
                        st.plotly_chart(fig_confidence_trend, use_container_width=True)
                else:
                    st.info("Not enough data points to show trends. Check back after more jobs have been analyzed.")
            else:
                st.info("Not enough jobs to display trends. Try expanding your time range or check back later.")
        
        # Export functionality
        st.subheader("📥 Export Data")
        col1, col2 = st.columns(2)
        
        with col1:
            # Export filtered results as CSV
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📊 Download CSV",
                data=csv_data,
                file_name=f"reddit_jobs_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Export as JSON
            json_data = df.to_json(orient='records', date_format='iso')
            st.download_button(
                label="📋 Download JSON",
                data=json_data,
                file_name=f"reddit_jobs_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )
    
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.info("Make sure the database exists and the scraper has been run at least once.")
        
        # Show database stats if available
        try:
            stats = get_database_stats()
            st.write("Database Stats:", stats)
        except:
            st.write("Could not connect to database.")

# Refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.experimental_rerun()

    # Display current filter stats in sidebar
    if 'df' in locals() and len(df) > 0:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 Current Results")
        st.sidebar.metric("Matching Jobs", len(df))
        
        if len(df) > 0:
            worth_count = df['worth_checking'].sum()
            st.sidebar.metric("Worth Checking", f"{worth_count}/{len(df)}")
            
            avg_conf = df['confidence_score'].mean()
            st.sidebar.metric("Avg Confidence", f"{avg_conf:.0f}%")
            
            remote_count = df['remote_friendly'].sum()
            st.sidebar.metric("Remote Jobs", f"{remote_count}/{len(df)}")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Reddit Job Scraper Dashboard**")
st.sidebar.markdown("Built with ❤️ using Streamlit")

if __name__ == "__main__":
    main()