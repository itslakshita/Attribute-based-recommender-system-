import os
import streamlit as st
import sqlite3
import json
import pandas as pd
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'pro_recommender.db')

st.set_page_config(page_title="Pro Attribute Recommender", layout="wide")

# Modern UI Styling
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .user-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 15px; margin: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'user_preferences' not in st.session_state:
    st.session_state.user_preferences = {}

# Database connection with error handling
@st.cache_resource
def get_db_connection():
    """Create and cache database connection"""
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        st.error(f"Database connection failed: {e}")
        st.stop()

try:
    conn = get_db_connection()
    cursor = conn.cursor()
except Exception as e:
    st.error(f"Failed to initialize database: {e}")
    st.stop()

# Helper functions
def get_user_profile(user_id):
    """Get user profile from database with error handling"""
    try:
        cursor.execute("SELECT * FROM User_Profiles WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'preferred_categories': json.loads(user[2]) if user[2] else [],
                'preferred_brands': json.loads(user[3]) if user[3] else [],
                'budget_range': user[4],
                'min_rating': user[5],
                'favorite_specs': json.loads(user[6]) if user[6] else []
            }
        return None
    except Exception as e:
        st.error(f"Error fetching user profile: {e}")
        return None

def save_user_interaction(user_id, product_id, interaction_type, rating=None):
    """Save user interaction to database with error handling"""
    try:
        cursor.execute("""
            INSERT INTO User_Product_Interactions (user_id, product_id, interaction_type, rating)
            VALUES (?, ?, ?, ?)
        """, (user_id, product_id, interaction_type, rating))
        conn.commit()
    except Exception as e:
        st.error(f"Error saving interaction: {e}")

def get_personalized_recommendations(user_id):
    """Generate personalized recommendations based on user's liked products"""
    try:
        # Get user's liked products and their specs
        cursor.execute("""
            SELECT p.*, ps.attr_id, ps.attr_value
            FROM User_Product_Interactions upi
            JOIN Products p ON upi.product_id = p.id
            LEFT JOIN Product_Specs ps ON p.id = ps.p_id
            WHERE upi.user_id = ? AND upi.interaction_type = 'liked'
        """, (user_id,))
        liked_products = cursor.fetchall()

        if not liked_products:
            return []

        # Find similar products based on specs and category
        liked_product_ids = list(set([p[0] for p in liked_products]))
        liked_specs = list(set([p[8] + ': ' + p[9] for p in liked_products if p[8] and p[9]]))

        # Get products with similar specs
        recommendations = []
        for spec in liked_specs[:3]:  # Use top 3 specs
            attr_name, attr_value = spec.split(': ', 1)
            
            # Build query safely with parameterized values
            placeholders = ','.join(['?'] * len(liked_product_ids))
            query = f"""
                SELECT DISTINCT p.*, COUNT(*) as spec_matches
                FROM Products p
                JOIN Product_Specs ps ON p.id = ps.p_id
                WHERE ps.attr_id = ? AND ps.attr_value = ?
                AND p.id NOT IN ({placeholders})
                GROUP BY p.id
                ORDER BY p.rating DESC, spec_matches DESC
                LIMIT 5
            """
            
            cursor.execute(query, [attr_name, attr_value] + liked_product_ids)
            recommendations.extend(cursor.fetchall())

        # Remove duplicates and sort by rating
        seen_ids = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec[0] not in seen_ids:
                unique_recommendations.append(rec)
                seen_ids.add(rec[0])

        return unique_recommendations[:8]
    except Exception as e:
        st.error(f"Error generating recommendations: {e}")
        return []

# Main App
st.title("🎯 Pro Attribute Recommender")
st.caption("AI-Inspired Database Engine for Precise Product Needs")

# User Profile Section
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    if st.session_state.current_user:
        user_profile = get_user_profile(st.session_state.current_user)
        if user_profile:
            st.markdown(f"""
            <div class="user-card">
            <h3>👋 Welcome back, {user_profile['username']}!</h3>
            <p>Preferred categories: {', '.join(user_profile['preferred_categories']) if user_profile['preferred_categories'] else 'None selected'}</p>
            <p>Budget range: ${user_profile['budget_range'] if user_profile['budget_range'] else 'Not set'}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("👤 Sign in to get personalized recommendations!")

with col2:
    if st.button("🔄 Switch User" if st.session_state.current_user else "👤 Sign In"):
        # Simple user selection (in real app, this would be proper authentication)
        try:
            cursor.execute("SELECT id, username FROM User_Profiles")
            users = cursor.fetchall()
            user_options = ["Guest"] + [f"{u[1]} (ID: {u[0]})" for u in users]

            selected_user = st.selectbox("Select User Profile:", user_options, key="user_selector")

            if selected_user != "Guest":
                user_id = int(selected_user.split("(ID: ")[1].rstrip(")"))
                st.session_state.current_user = user_id
                st.session_state.user_preferences = get_user_profile(user_id)
                st.rerun()
            else:
                st.session_state.current_user = None
                st.session_state.user_preferences = {}
                st.rerun()
        except Exception as e:
            st.error(f"Error loading users: {e}")

with col3:
    if st.session_state.current_user and st.button("🚪 Sign Out"):
        st.session_state.current_user = None
        st.session_state.user_preferences = {}
        st.rerun()

# Main Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Smart Search", "💡 Personalized Recs", "⭐ My Activity", "📊 Analytics"])

with tab1:
    st.header("Smart Product Search")

    # Auto-fill preferences if user is logged in
    categories = ["Laptops", "Audio", "Smartphones", "Tablets", "Gaming", "Cameras"]
    default_category = st.session_state.user_preferences.get('preferred_categories', ["Laptops"])[0] if st.session_state.user_preferences else "Laptops"
    default_budget = 1000
    default_rating = 4
    
    if st.session_state.user_preferences and st.session_state.user_preferences.get('budget_range'):
        try:
            default_budget = int(st.session_state.user_preferences.get('budget_range', '1000').split('-')[1])
        except:
            default_budget = 1000
    
    if st.session_state.user_preferences:
        default_rating = int(st.session_state.user_preferences.get('min_rating', 4))

    filter_col, result_col = st.columns([1, 2], gap="large")

    with filter_col:
        st.subheader("Search Preferences")
        category = st.selectbox(
            "Category",
            categories,
            index=categories.index(default_category) if default_category in categories else 0
        )
        max_price = st.slider("Max Budget", 100, 5000, default_budget)
        min_rating = st.select_slider("Minimum Rating", options=[1, 2, 3, 4, 5], value=default_rating)

        st.markdown("### Advanced Filters")
        color_pref = st.multiselect(
            "Color Preferences",
            ["Grey", "Silver", "Black", "Gold", "Blue", "White"],
            default=[]
        )
        brand_pref = st.multiselect(
            "Preferred Brands",
            ["Apple", "Samsung", "ASUS", "Dell", "Sony", "Lenovo", "Google", "OnePlus", "Bose", "Canon", "Nikon"],
            default=[]
        )

    with result_col:
        st.subheader("💡 Recommended Specs")
        st.info("Based on your preferences and budget, here are the most popular specs:")

        try:
            # Get category ID
            cursor.execute("SELECT id FROM Categories WHERE name = ?", (category,))
            result = cursor.fetchone()
            if not result:
                st.error(f"Category '{category}' not found")
            else:
                cat_id = result[0]

                # Log search history
                user_id = st.session_state.current_user or 0
                cursor.execute("INSERT INTO Search_History (user_id, category, max_price, min_rating) VALUES (?, ?, ?, ?)",
                               (user_id, category, max_price, min_rating))
                conn.commit()

                # Build attribute query
                attr_query = '''
                    SELECT ps.attr_id, ps.attr_value, COUNT(*) as score
                    FROM Product_Specs ps
                    JOIN Products p ON ps.p_id = p.id
                    WHERE p.price <= ? AND p.rating >= ? AND p.cat_id = ?
                '''
                attr_params = [max_price, min_rating, cat_id]

                if color_pref:
                    attr_query += " AND p.color IN ({})".format(','.join(['?'] * len(color_pref)))
                    attr_params.extend(color_pref)
                if brand_pref:
                    attr_query += " AND p.brand IN ({})".format(','.join(['?'] * len(brand_pref)))
                    attr_params.extend(brand_pref)

                attr_query += '''
                    GROUP BY ps.attr_id, ps.attr_value
                    ORDER BY score DESC
                    LIMIT 8
                '''

                cursor.execute(attr_query, attr_params)
                recommendations = cursor.fetchall()

                if recommendations:
                    for i, r in enumerate(recommendations):
                        st.write(f"**{i+1}. {r[0]}**: {r[1]}")
                        st.progress(min(r[2] * 15, 100))
                else:
                    st.write("No specific patterns found for your criteria.")

                st.markdown("---")
                st.subheader("📦 Matching Products")

                prod_query = '''
                    SELECT id, name, brand, price, rating, color, stock_status
                    FROM Products
                    WHERE price <= ? AND rating >= ? AND cat_id = ?
                '''
                prod_params = [max_price, min_rating, cat_id]

                if color_pref:
                    prod_query += " AND color IN ({})".format(','.join(['?'] * len(color_pref)))
                    prod_params.extend(color_pref)
                if brand_pref:
                    prod_query += " AND brand IN ({})".format(','.join(['?'] * len(brand_pref)))
                    prod_params.extend(brand_pref)

                prod_query += " ORDER BY rating DESC, price ASC"

                cursor.execute(prod_query, prod_params)
                products = cursor.fetchall()

                if not products:
                    st.error("No products match your refined criteria. Try adjusting filters.")
                else:
                    for p in products:
                        with st.container():
                            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                            c1.markdown(f"### {p[1]}")
                            c1.caption(f"Brand: {p[2]} | Color: {p[5]} | Stock: {p[6]}")
                            c2.markdown(f"**Price**\n${p[3]}")
                            c3.markdown(f"**Rating**\n⭐ {p[4]}")

                            if st.session_state.current_user:
                                if c4.button("👍 Like", key=f"like_{p[0]}"): 
                                    save_user_interaction(st.session_state.current_user, p[0], 'liked', p[4])
                                    st.success("Added to liked products!")
                                if c4.button("💾 Save", key=f"save_{p[0]}"):
                                    save_user_interaction(st.session_state.current_user, p[0], 'saved')
                                    st.success("Saved to wishlist!")
                            else:
                                c4.caption("Sign in to save")

                            st.divider()
        except Exception as e:
            st.error(f"Error performing search: {e}")

with tab2:
    st.header("🎯 Personalized Recommendations")

    if not st.session_state.current_user:
        st.warning("Please sign in to see personalized recommendations based on your preferences and past interactions.")
        st.info("💡 Personalized recommendations learn from your liked products and search history to suggest items you'll love!")
    else:
        try:
            user_profile = get_user_profile(st.session_state.current_user)
            if user_profile:
                # Show user preferences
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Your Preferences")
                    st.write(f"**Favorite Categories:** {', '.join(user_profile['preferred_categories']) if user_profile['preferred_categories'] else 'Not set'}")
                    st.write(f"**Preferred Brands:** {', '.join(user_profile['preferred_brands']) if user_profile['preferred_brands'] else 'Not set'}")
                    st.write(f"**Budget Range:** ${user_profile['budget_range'] if user_profile['budget_range'] else 'Not set'}")
                    st.write(f"**Minimum Rating:** ⭐ {user_profile['min_rating']}")

                with col2:
                    st.subheader("Your Favorite Specs")
                    if user_profile['favorite_specs']:
                        for spec in user_profile['favorite_specs'][:5]:
                            st.write(f"• {spec}")
                    else:
                        st.write("No favorite specs yet")

                # Get personalized recommendations
                st.subheader("🔥 Recommended for You")
                personalized_recs = get_personalized_recommendations(st.session_state.current_user)

                if personalized_recs:
                    for p in personalized_recs:
                        with st.container():
                            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                            c1.markdown(f"### {p[1]}")
                            c1.caption(f"Brand: {p[2]} | Color: {p[5]} | Stock: {p[6]}")
                            c2.markdown(f"**Price**\n${p[3]}")
                            c3.markdown(f"**Rating**\n⭐ {p[4]}")

                            if c4.button("👍 Like", key=f"personal_like_{p[0]}"):
                                save_user_interaction(st.session_state.current_user, p[0], 'liked', p[4])
                                st.success("Added to liked products!")
                            if c4.button("💾 Save", key=f"personal_save_{p[0]}"):
                                save_user_interaction(st.session_state.current_user, p[0], 'saved')
                                st.success("Saved to wishlist!")

                            st.divider()
                else:
                    st.info("Start liking products to get personalized recommendations! The more you interact, the better our suggestions become.")
        except Exception as e:
            st.error(f"Error loading recommendations: {e}")

with tab3:
    st.header("⭐ My Activity & Wishlist")

    if not st.session_state.current_user:
        st.warning("Sign in to view your activity and saved items.")
    else:
        try:
            # Get user's interactions
            cursor.execute("""
                SELECT p.name, p.brand, p.price, p.rating, upi.interaction_type, upi.timestamp
                FROM User_Product_Interactions upi
                JOIN Products p ON upi.product_id = p.id
                WHERE upi.user_id = ?
                ORDER BY upi.timestamp DESC
            """, (st.session_state.current_user,))

            interactions = cursor.fetchall()

            if interactions:
                st.subheader("Your Recent Activity")

                # Group by interaction type
                liked = [i for i in interactions if i[4] == 'liked']
                saved = [i for i in interactions if i[4] == 'saved']
                viewed = [i for i in interactions if i[4] == 'viewed']

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown(f"**❤️ Liked Products**\n{len(liked)}")
                    if liked:
                        st.write("**Recently Liked:**")
                        for item in liked[:3]:
                            st.write(f"• {item[0]} (⭐ {item[3]})")

                with col2:
                    st.markdown(f"**💾 Saved Items**\n{len(saved)}")
                    if saved:
                        st.write("**Your Wishlist:**")
                        for item in saved[:3]:
                            st.write(f"• {item[0]} (${item[2]})")

                with col3:
                    st.markdown(f"**👁️ Viewed Products**\n{len(viewed)}")
                    if viewed:
                        st.write("**Recently Viewed:**")
                        for item in viewed[:3]:
                            st.write(f"• {item[0]}")

                # Detailed activity log
                with st.expander("View Full Activity Log"):
                    for interaction in interactions:
                        st.write(f"{interaction[5]} - {interaction[4].title()}: {interaction[0]} by {interaction[1]}")
            else:
                st.info("No activity yet! Start exploring products to build your personalized experience.")
        except Exception as e:
            st.error(f"Error loading activity: {e}")

with tab4:
    st.header("📊 Analytics Dashboard")

    # Search History Trends
    st.subheader("🔍 Search Trends")
    try:
        history_query = """
            SELECT category, ROUND(AVG(max_price), 0) as avg_budget, ROUND(AVG(min_rating), 1) as avg_rating, COUNT(*) as searches
            FROM Search_History
            GROUP BY category
            ORDER BY searches DESC
        """
        cursor.execute(history_query)
        history = cursor.fetchall()

        if history:
            for h in history:
                st.write(f"**{h[0]}**: Avg Budget ${h[1]}, Avg Rating ⭐{h[2]} ({h[3]} searches)")
        else:
            st.write("No search history yet.")
    except Exception as e:
        st.error(f"Error loading analytics: {e}")
