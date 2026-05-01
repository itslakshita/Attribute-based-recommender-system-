import os
import sqlite3

db_path = os.path.join(os.path.dirname(__file__), 'pro_recommender.db')

def setup_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Optimized Tables
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS Categories (id INTEGER PRIMARY KEY, name TEXT);
        
        CREATE TABLE IF NOT EXISTS Products (
            id INTEGER PRIMARY KEY, 
            name TEXT, 
            cat_id INTEGER, 
            price REAL, 
            brand TEXT,
            rating REAL,
            color TEXT,
            stock_status TEXT
        );

        CREATE TABLE IF NOT EXISTS Attributes (id INTEGER PRIMARY KEY, name TEXT, type TEXT);

        CREATE TABLE IF NOT EXISTS Product_Specs (
            id INTEGER PRIMARY KEY, 
            p_id INTEGER, 
            attr_id TEXT, 
            attr_value TEXT,
            FOREIGN KEY(p_id) REFERENCES Products(id)
        );

        CREATE TABLE IF NOT EXISTS Search_History (
            id INTEGER PRIMARY KEY,
            category TEXT,
            max_price REAL,
            min_rating REAL,
            search_time DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # Add user_id column if it doesn't exist (for backward compatibility)
    cursor.execute("PRAGMA table_info(Search_History)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'user_id' not in columns:
        cursor.execute("ALTER TABLE Search_History ADD COLUMN user_id INTEGER DEFAULT 0")

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS User_Profiles (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            preferred_categories TEXT, -- JSON string of preferred categories
            preferred_brands TEXT, -- JSON string of preferred brands
            budget_range TEXT, -- JSON string like "500-1500"
            min_rating REAL DEFAULT 4.0,
            favorite_specs TEXT, -- JSON string of favorite specifications
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS User_Product_Interactions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            product_id INTEGER,
            interaction_type TEXT, -- 'viewed', 'saved', 'liked', 'disliked'
            rating REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES User_Profiles(id),
            FOREIGN KEY(product_id) REFERENCES Products(id)
        );
        
        -- Index for speed (Optimizing queries)
        CREATE INDEX IF NOT EXISTS idx_prod_search ON Products(price, rating, cat_id);
    ''')

    # Seed Data
    categories = [
        (1, 'Laptops'),
        (2, 'Audio'),
        (3, 'Smartphones'),
        (4, 'Tablets'),
        (5, 'Gaming'),
        (6, 'Cameras')
    ]
    cursor.executemany('INSERT OR IGNORE INTO Categories VALUES (?,?)', categories)
    
    # Adding Rating and Color to Products
    products = [
        # Laptops (cat_id=1)
        (1, 'ZenBook 14', 1, 950.0, 'ASUS', 4.8, 'Pine Grey', 'In Stock'),
        (2, 'MacBook Air', 1, 1100.0, 'Apple', 4.9, 'Space Grey', 'In Stock'),
        (3, 'Inspiron 15', 1, 600.0, 'Dell', 4.2, 'Platinum Silver', 'Low Stock'),
        (4, 'ThinkPad X1', 1, 1400.0, 'Lenovo', 4.7, 'Black', 'In Stock'),
        (5, 'Surface Laptop 4', 1, 1200.0, 'Microsoft', 4.6, 'Platinum', 'In Stock'),
        (6, 'ROG Zephyrus', 1, 1800.0, 'ASUS', 4.8, 'Eclipse Grey', 'In Stock'),
        (7, 'MacBook Pro 16', 1, 2500.0, 'Apple', 4.9, 'Space Grey', 'In Stock'),
        (8, 'XPS 13', 1, 1300.0, 'Dell', 4.5, 'Silver', 'In Stock'),
        (9, 'Yoga 9i', 1, 1600.0, 'Lenovo', 4.4, 'Mica', 'Low Stock'),
        (10, 'Spectre x360', 1, 1500.0, 'HP', 4.6, 'Nightfall Black', 'In Stock'),
        
        # Audio (cat_id=2)
        (11, 'QuietComfort 45', 2, 320.0, 'Bose', 4.7, 'Black', 'In Stock'),
        (12, 'AirPods Pro', 2, 250.0, 'Apple', 4.6, 'White', 'In Stock'),
        (13, 'WH-1000XM4', 2, 350.0, 'Sony', 4.8, 'Black', 'In Stock'),
        (14, 'Galaxy Buds Pro', 2, 200.0, 'Samsung', 4.4, 'Phantom Black', 'In Stock'),
        (15, 'Soundcore Liberty', 2, 150.0, 'Anker', 4.3, 'Black', 'In Stock'),
        (16, 'Momentum Wireless', 2, 400.0, 'Sennheiser', 4.5, 'Black', 'Low Stock'),
        (17, 'Elite 7 Active', 2, 180.0, 'Jabra', 4.2, 'Black', 'In Stock'),
        (18, 'Pixel Buds Pro', 2, 220.0, 'Google', 4.1, 'Fog', 'In Stock'),
        
        # Smartphones (cat_id=3)
        (19, 'iPhone 15 Pro', 3, 1200.0, 'Apple', 4.8, 'Titanium Natural', 'In Stock'),
        (20, 'Galaxy S24 Ultra', 3, 1300.0, 'Samsung', 4.7, 'Titanium Black', 'In Stock'),
        (21, 'Pixel 8 Pro', 3, 1000.0, 'Google', 4.5, 'Porcelain', 'In Stock'),
        (22, 'OnePlus 12', 3, 800.0, 'OnePlus', 4.4, 'Silky Black', 'In Stock'),
        (23, 'Xperia 1 V', 3, 1400.0, 'Sony', 4.3, 'Black', 'Low Stock'),
        (24, 'iPhone 15', 3, 900.0, 'Apple', 4.6, 'Blue', 'In Stock'),
        (25, 'Galaxy S24', 3, 800.0, 'Samsung', 4.4, 'Marble Grey', 'In Stock'),
        (26, 'Pixel 8', 3, 700.0, 'Google', 4.3, 'Mint', 'In Stock'),
        
        # Tablets (cat_id=4)
        (27, 'iPad Pro 12.9', 4, 1100.0, 'Apple', 4.8, 'Space Grey', 'In Stock'),
        (28, 'Galaxy Tab S9', 4, 800.0, 'Samsung', 4.6, 'Graphite', 'In Stock'),
        (29, 'Surface Pro 9', 4, 1000.0, 'Microsoft', 4.5, 'Platinum', 'In Stock'),
        (30, 'iPad Air', 4, 600.0, 'Apple', 4.7, 'Blue', 'In Stock'),
        (31, 'Galaxy Tab S8', 4, 700.0, 'Samsung', 4.4, 'Silver', 'In Stock'),
        (32, 'Lenovo Tab P12', 4, 500.0, 'Lenovo', 4.2, 'Storm Grey', 'In Stock'),
        
        # Gaming (cat_id=5)
        (33, 'ROG Strix G15', 5, 1600.0, 'ASUS', 4.7, 'Eclipse Grey', 'In Stock'),
        (34, 'Alienware m15', 5, 2200.0, 'Dell', 4.6, 'Dark Side of the Moon', 'In Stock'),
        (35, 'Legion 5 Pro', 5, 1400.0, 'Lenovo', 4.5, 'Storm Grey', 'In Stock'),
        (36, 'Predator Helios', 5, 1800.0, 'Acer', 4.4, 'Abyssal Black', 'Low Stock'),
        (37, 'GS66 Stealth', 5, 2000.0, 'MSI', 4.8, 'Core Black', 'In Stock'),
        
        # Cameras (cat_id=6)
        (38, 'EOS R5', 6, 3900.0, 'Canon', 4.8, 'Black', 'In Stock'),
        (39, 'α7R V', 6, 4200.0, 'Sony', 4.9, 'Black', 'In Stock'),
        (40, 'D850', 6, 3300.0, 'Nikon', 4.7, 'Black', 'Low Stock'),
        (41, 'X-T5', 6, 1700.0, 'Fujifilm', 4.6, 'Black', 'In Stock'),
        (42, 'OM-1', 6, 2200.0, 'Olympus', 4.5, 'Black', 'In Stock')
    ]
    cursor.executemany('INSERT OR IGNORE INTO Products VALUES (?,?,?,?,?,?,?,?)', products)

    # Specific Specs for the "Attribute Recommender"
    specs = [
        # Laptops
        (1, 1, 'Build', 'Aluminum'), (2, 1, 'Display', 'OLED'), (3, 1, 'Processor', 'Intel i7'), (4, 1, 'RAM', '16GB'), (5, 1, 'Storage', '512GB SSD'),
        (6, 2, 'Build', 'Aluminum'), (7, 2, 'Display', 'Retina'), (8, 2, 'Processor', 'Apple M2'), (9, 2, 'RAM', '8GB'), (10, 2, 'Storage', '256GB SSD'),
        (11, 3, 'Build', 'Plastic'), (12, 3, 'Display', 'LCD'), (13, 3, 'Processor', 'Intel i5'), (14, 3, 'RAM', '8GB'), (15, 3, 'Storage', '256GB SSD'),
        (16, 4, 'Build', 'Carbon Fiber'), (17, 4, 'Display', 'IPS'), (18, 4, 'Processor', 'Intel i7'), (19, 4, 'RAM', '16GB'), (20, 4, 'Storage', '1TB SSD'),
        (21, 5, 'Build', 'Aluminum'), (22, 5, 'Display', 'PixelSense'), (23, 5, 'Processor', 'Intel i5'), (24, 5, 'RAM', '8GB'), (25, 5, 'Storage', '256GB SSD'),
        (26, 6, 'Build', 'Aluminum'), (27, 6, 'Display', 'IPS'), (28, 6, 'Processor', 'AMD Ryzen 9'), (29, 6, 'RAM', '32GB'), (30, 6, 'Storage', '1TB SSD'),
        (31, 7, 'Build', 'Aluminum'), (32, 7, 'Display', 'Liquid Retina XDR'), (33, 7, 'Processor', 'Apple M3 Max'), (34, 7, 'RAM', '32GB'), (35, 7, 'Storage', '1TB SSD'),
        (36, 8, 'Build', 'Carbon Fiber'), (37, 8, 'Display', 'InfinityEdge'), (38, 8, 'Processor', 'Intel i7'), (39, 8, 'RAM', '16GB'), (40, 8, 'Storage', '512GB SSD'),
        (41, 9, 'Build', 'Aluminum'), (42, 9, 'Display', 'IPS'), (43, 9, 'Processor', 'Intel i7'), (44, 9, 'RAM', '16GB'), (45, 9, 'Storage', '1TB SSD'),
        (46, 10, 'Build', 'Aluminum'), (47, 10, 'Display', 'OLED'), (48, 10, 'Processor', 'Intel i7'), (49, 10, 'RAM', '16GB'), (50, 10, 'Storage', '1TB SSD'),
        
        # Audio
        (51, 11, 'Type', 'Over-Ear'), (52, 11, 'ANC', 'Yes'), (53, 11, 'Battery', '24h'), (54, 11, 'Connectivity', 'Bluetooth 5.1'),
        (55, 12, 'Type', 'In-Ear'), (56, 12, 'ANC', 'Yes'), (57, 12, 'Battery', '6h'), (58, 12, 'Connectivity', 'Bluetooth 5.0'),
        (59, 13, 'Type', 'Over-Ear'), (60, 13, 'ANC', 'Yes'), (61, 13, 'Battery', '30h'), (62, 13, 'Connectivity', 'Bluetooth 5.0'),
        (63, 14, 'Type', 'In-Ear'), (64, 14, 'ANC', 'Yes'), (65, 14, 'Battery', '8h'), (66, 14, 'Connectivity', 'Bluetooth 5.3'),
        (67, 15, 'Type', 'In-Ear'), (68, 15, 'ANC', 'Yes'), (69, 15, 'Battery', '9h'), (70, 15, 'Connectivity', 'Bluetooth 5.0'),
        (71, 16, 'Type', 'Over-Ear'), (72, 16, 'ANC', 'Yes'), (73, 16, 'Battery', '17h'), (74, 16, 'Connectivity', 'Bluetooth 5.1'),
        (75, 17, 'Type', 'In-Ear'), (76, 17, 'ANC', 'Yes'), (77, 17, 'Battery', '8h'), (78, 17, 'Connectivity', 'Bluetooth 5.0'),
        (79, 18, 'Type', 'In-Ear'), (80, 18, 'ANC', 'Yes'), (81, 18, 'Battery', '7h'), (82, 18, 'Connectivity', 'Bluetooth 5.2'),
        
        # Smartphones
        (83, 19, 'Display', '6.1" Super Retina XDR'), (84, 19, 'Processor', 'A17 Pro'), (85, 19, 'RAM', '8GB'), (86, 19, 'Storage', '256GB'), (87, 19, 'Camera', '48MP'),
        (88, 20, 'Display', '6.8" Dynamic AMOLED'), (89, 20, 'Processor', 'Snapdragon 8 Gen 3'), (90, 20, 'RAM', '12GB'), (91, 20, 'Storage', '512GB'), (92, 20, 'Camera', '200MP'),
        (93, 21, 'Display', '6.7" LTPO OLED'), (94, 21, 'Processor', 'Google Tensor G3'), (95, 21, 'RAM', '12GB'), (96, 21, 'Storage', '256GB'), (97, 21, 'Camera', '50MP'),
        (98, 22, 'Display', '6.82" AMOLED'), (99, 22, 'Processor', 'Snapdragon 8 Gen 3'), (100, 22, 'RAM', '16GB'), (101, 22, 'Storage', '256GB'), (102, 22, 'Camera', '50MP'),
        (103, 23, 'Display', '6.5" OLED'), (104, 23, 'Processor', 'Snapdragon 8 Gen 2'), (105, 23, 'RAM', '12GB'), (106, 23, 'Storage', '256GB'), (107, 23, 'Camera', '52MP'),
        (108, 24, 'Display', '6.1" Super Retina XDR'), (109, 24, 'Processor', 'A16 Bionic'), (110, 24, 'RAM', '6GB'), (111, 24, 'Storage', '128GB'), (112, 24, 'Camera', '48MP'),
        (113, 25, 'Display', '6.2" Dynamic AMOLED'), (114, 25, 'Processor', 'Exynos 2400'), (115, 25, 'RAM', '8GB'), (116, 25, 'Storage', '256GB'), (117, 25, 'Camera', '50MP'),
        (118, 26, 'Display', '6.2" OLED'), (119, 26, 'Processor', 'Google Tensor G3'), (120, 26, 'RAM', '8GB'), (121, 26, 'Storage', '128GB'), (122, 26, 'Camera', '50MP'),
        
        # Tablets
        (123, 27, 'Display', '12.9" Liquid Retina XDR'), (124, 27, 'Processor', 'M2'), (125, 27, 'RAM', '8GB'), (126, 27, 'Storage', '256GB'), (127, 27, 'Camera', '12MP'),
        (128, 28, 'Display', '11" Dynamic AMOLED'), (129, 28, 'Processor', 'Snapdragon 8 Gen 2'), (130, 28, 'RAM', '8GB'), (131, 28, 'Storage', '128GB'), (132, 28, 'Camera', '13MP'),
        (133, 29, 'Display', '13" PixelSense'), (134, 29, 'Processor', 'Intel i5'), (135, 29, 'RAM', '8GB'), (136, 29, 'Storage', '256GB'), (137, 29, 'Camera', '10MP'),
        (138, 30, 'Display', '10.9" Liquid Retina'), (139, 30, 'Processor', 'M1'), (140, 30, 'RAM', '8GB'), (141, 30, 'Storage', '64GB'), (142, 30, 'Camera', '12MP'),
        (143, 31, 'Display', '11" TFT'), (144, 31, 'Processor', 'Snapdragon 8 Gen 2'), (145, 31, 'RAM', '8GB'), (146, 31, 'Storage', '128GB'), (147, 31, 'Camera', '13MP'),
        (148, 32, 'Display', '12.7" IPS'), (149, 32, 'Processor', 'MediaTek Kompanio 1300T'), (150, 32, 'RAM', '8GB'), (151, 32, 'Storage', '128GB'), (152, 32, 'Camera', '13MP'),
        
        # Gaming Laptops
        (153, 33, 'Build', 'Plastic'), (154, 33, 'Display', 'IPS'), (155, 33, 'Processor', 'AMD Ryzen 7'), (156, 33, 'RAM', '16GB'), (157, 33, 'Storage', '512GB SSD'), (158, 33, 'GPU', 'RTX 4060'),
        (159, 34, 'Build', 'Plastic'), (160, 34, 'Display', 'IPS'), (161, 34, 'Processor', 'Intel i9'), (162, 34, 'RAM', '32GB'), (163, 34, 'Storage', '1TB SSD'), (164, 34, 'GPU', 'RTX 4080'),
        (165, 35, 'Build', 'Aluminum'), (166, 35, 'Display', 'IPS'), (167, 35, 'Processor', 'AMD Ryzen 7'), (168, 35, 'RAM', '16GB'), (169, 35, 'Storage', '512GB SSD'), (170, 35, 'GPU', 'RTX 4060'),
        (171, 36, 'Build', 'Plastic'), (172, 36, 'Display', 'IPS'), (173, 36, 'Processor', 'Intel i7'), (174, 36, 'RAM', '16GB'), (175, 36, 'Storage', '512GB SSD'), (176, 36, 'GPU', 'RTX 4070'),
        (177, 37, 'Build', 'Aluminum'), (178, 37, 'Display', 'IPS'), (179, 37, 'Processor', 'Intel i9'), (180, 37, 'RAM', '32GB'), (181, 37, 'Storage', '1TB SSD'), (182, 37, 'GPU', 'RTX 4080'),
        
        # Cameras
        (183, 38, 'Sensor', '45MP Full-Frame'), (184, 38, 'Video', '8K'), (185, 38, 'Lens Mount', 'RF'), (186, 38, 'ISO Range', '100-51200'),
        (187, 39, 'Sensor', '61MP Full-Frame'), (188, 39, 'Video', '8K'), (189, 39, 'Lens Mount', 'E-mount'), (190, 39, 'ISO Range', '100-102400'),
        (191, 40, 'Sensor', '45.7MP Full-Frame'), (192, 40, 'Video', '4K'), (193, 40, 'Lens Mount', 'F-mount'), (194, 40, 'ISO Range', '64-25600'),
        (195, 41, 'Sensor', '40MP APS-C'), (196, 41, 'Video', '6.2K'), (197, 41, 'Lens Mount', 'X-mount'), (198, 41, 'ISO Range', '160-12800'),
        (199, 42, 'Sensor', '20MP Micro Four Thirds'), (200, 42, 'Video', '4K'), (201, 42, 'Lens Mount', 'Micro Four Thirds'), (202, 42, 'ISO Range', '200-102400')
    ]
    cursor.executemany('INSERT OR IGNORE INTO Product_Specs VALUES (?,?,?,?)', specs)

    # Sample User Profiles
    user_profiles = [
        (1, 'tech_enthusiast', '["Laptops", "Gaming"]', '["ASUS", "Apple", "Dell"]', '1000-2000', 4.5, '["Aluminum Build", "SSD Storage", "High RAM"]', '2024-01-01'),
        (2, 'budget_buyer', '["Audio", "Tablets"]', '["Sony", "Samsung", "Anker"]', '100-500', 4.0, '["Good Battery", "Wireless", "Affordable"]', '2024-01-02'),
        (3, 'pro_photographer', '["Cameras", "Laptops"]', '["Canon", "Sony", "Nikon"]', '2000-4000', 4.7, '["Full Frame", "4K Video", "High ISO"]', '2024-01-03'),
        (4, 'mobile_user', '["Smartphones", "Audio"]', '["Apple", "Samsung", "Google"]', '500-1200', 4.2, '["Good Camera", "Fast Charging", "Large Display"]', '2024-01-04')
    ]
    cursor.executemany('INSERT OR IGNORE INTO User_Profiles VALUES (?,?,?,?,?,?,?,?)', user_profiles)

    # Sample User Interactions
    interactions = [
        (1, 1, 1, 'liked', 5.0, '2024-01-01 10:00:00'),
        (1, 1, 2, 'viewed', None, '2024-01-01 10:05:00'),
        (1, 1, 6, 'saved', 4.8, '2024-01-01 10:10:00'),
        (2, 2, 11, 'liked', 4.5, '2024-01-02 14:00:00'),
        (2, 2, 15, 'saved', 4.3, '2024-01-02 14:05:00'),
        (2, 2, 27, 'viewed', None, '2024-01-02 14:10:00'),
        (3, 3, 38, 'liked', 5.0, '2024-01-03 16:00:00'),
        (3, 3, 39, 'saved', 4.9, '2024-01-03 16:05:00'),
        (3, 3, 1, 'viewed', None, '2024-01-03 16:10:00'),
        (4, 4, 19, 'liked', 4.8, '2024-01-04 12:00:00'),
        (4, 4, 24, 'saved', 4.6, '2024-01-04 12:05:00'),
        (4, 4, 11, 'viewed', None, '2024-01-04 12:10:00')
    ]
    cursor.executemany('INSERT OR IGNORE INTO User_Product_Interactions VALUES (?,?,?,?,?,?)', interactions)

    conn.commit()
    conn.close()
    print("Database built and optimized!")

if __name__ == "__main__":
    setup_db();