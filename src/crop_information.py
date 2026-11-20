"""
KROP - Crop Information Module
Agronomic reference data curated from ICAR (Indian Council of Agricultural Research),
Ministry of Agriculture & Farmers Welfare, and State Agricultural Universities.
Strictly zero NPK. Contains purely agronomic, environmental, water, and soil requirements.
"""

from functools import lru_cache
from pathlib import Path
import pandas as pd
from typing import Dict, List, Optional

from src.config import CROP_INFO_CSV_PATH, PROCESSED_DATA_DIR

# Comprehensive authoritative agronomic database for major Indian crops
CROP_CATALOG = [
    {
        "crop_name": "Rice",
        "crop_category": "Cereals",
        "suitable_seasons": "Kharif, Summer, Autumn, Winter",
        "duration_min_days": 105,
        "duration_max_days": 150,
        "growing_duration_days": "105-150 days",
        "water_requirement": "High",
        "water_requirement_mm": "1100-1500 mm",
        "suitable_soil": "Clay, Clay Loam, Alluvial",
        "sowing_period": "June - July (Kharif), Nov - Dec (Rabi/Boro)",
        "min_temp_c": 20.0,
        "max_temp_c": 37.0,
        "temperature_conditions": "20°C - 37°C (warm and humid)",
        "cultivation_notes": "Needs standing water during early vegetative stages. Best suited for areas with assured canal/borewell irrigation or high monsoon rainfall.",
        "regional_information": "Widely grown in West Bengal, Uttar Pradesh, Punjab, Andhra Pradesh, Odisha, Tamil Nadu, Bihar, Assam, and Chhattisgarh.",
        "information_source": "ICAR - National Rice Research Institute (NRRI), Cuttack"
    },
    {
        "crop_name": "Wheat",
        "crop_category": "Cereals",
        "suitable_seasons": "Rabi",
        "duration_min_days": 110,
        "duration_max_days": 140,
        "growing_duration_days": "110-140 days",
        "water_requirement": "Medium",
        "water_requirement_mm": "450-650 mm",
        "suitable_soil": "Alluvial, Loamy, Clay Loam",
        "sowing_period": "November - December",
        "min_temp_c": 10.0,
        "max_temp_c": 25.0,
        "temperature_conditions": "10°C - 25°C (cool winter during vegetative, warm during grain ripening)",
        "cultivation_notes": "Sensitive to early heat stress during grain filling. Requires 4-6 critical irrigations (crown root initiation, tillering, flowering, milking).",
        "regional_information": "Dominant in Indo-Gangetic plains: Uttar Pradesh, Punjab, Haryana, Madhya Pradesh, Rajasthan, and Bihar.",
        "information_source": "ICAR - Indian Institute of Wheat and Barley Research (IIWBR), Karnal"
    },
    {
        "crop_name": "Maize",
        "crop_category": "Cereals",
        "suitable_seasons": "Kharif, Rabi, Summer",
        "duration_min_days": 85,
        "duration_max_days": 115,
        "growing_duration_days": "85-115 days",
        "water_requirement": "Medium",
        "water_requirement_mm": "500-750 mm",
        "suitable_soil": "Well-drained Loamy, Sandy Loam, Red Loam, Alluvial",
        "sowing_period": "June - July (Kharif), October - November (Rabi)",
        "min_temp_c": 18.0,
        "max_temp_c": 35.0,
        "temperature_conditions": "18°C - 35°C (warm, sunny weather)",
        "cultivation_notes": "Extremely versatile cereal. Highly intolerant of waterlogging; requires well-drained soils with good organic mulch.",
        "regional_information": "Karnataka, Madhya Pradesh, Maharashtra, Rajasthan, Bihar, Andhra Pradesh, Telangana, and Uttar Pradesh.",
        "information_source": "ICAR - Indian Institute of Maize Research (IIMR), Ludhiana"
    },
    {
        "crop_name": "Jowar",
        "crop_category": "Cereals",
        "suitable_seasons": "Kharif, Rabi",
        "duration_min_days": 95,
        "duration_max_days": 120,
        "growing_duration_days": "95-120 days",
        "water_requirement": "Low",
        "water_requirement_mm": "350-500 mm",
        "suitable_soil": "Black soil, Medium Deep Loamy, Clay Loam",
        "sowing_period": "June - July (Kharif), September - October (Rabi)",
        "min_temp_c": 20.0,
        "max_temp_c": 38.0,
        "temperature_conditions": "20°C - 38°C (drought-tolerant, warm dry climate)",
        "cultivation_notes": "Major drought-resilient millet. Thrives in semi-arid dryland conditions where other cereals fail.",
        "regional_information": "Maharashtra, Karnataka, Rajasthan, Andhra Pradesh, Tamil Nadu, Madhya Pradesh, and Gujarat.",
        "information_source": "ICAR - Indian Institute of Millets Research (IIMR), Hyderabad"
    },
    {
        "crop_name": "Bajra",
        "crop_category": "Cereals",
        "suitable_seasons": "Kharif, Summer",
        "duration_min_days": 75,
        "duration_max_days": 95,
        "growing_duration_days": "75-95 days",
        "water_requirement": "Low",
        "water_requirement_mm": "250-400 mm",
        "suitable_soil": "Sandy, Sandy Loam, Light Red Soil",
        "sowing_period": "June - July",
        "min_temp_c": 22.0,
        "max_temp_c": 42.0,
        "temperature_conditions": "22°C - 42°C (high heat tolerance, dry sunny weather)",
        "cultivation_notes": "Ideal for arid and semi-arid tracts with shallow sandy soils and erratic rainfall. Excellent fodder and nutrition value.",
        "regional_information": "Rajasthan, Uttar Pradesh, Gujarat, Haryana, Maharashtra, and Madhya Pradesh.",
        "information_source": "ICAR - All India Coordinated Research Project on Pearl Millet (AICRP-PM)"
    },
    {
        "crop_name": "Barley",
        "crop_category": "Cereals",
        "suitable_seasons": "Rabi",
        "duration_min_days": 115,
        "duration_max_days": 135,
        "growing_duration_days": "115-135 days",
        "water_requirement": "Low",
        "water_requirement_mm": "300-450 mm",
        "suitable_soil": "Sandy Loam, Loamy, Alluvial, Saline-tolerant",
        "sowing_period": "October - November",
        "min_temp_c": 12.0,
        "max_temp_c": 26.0,
        "temperature_conditions": "12°C - 26°C (cool and dry winter)",
        "cultivation_notes": "Significantly more salt-tolerant and drought-tolerant than wheat. Suitable for marginal soils in north-western plains.",
        "regional_information": "Rajasthan, Uttar Pradesh, Madhya Pradesh, Haryana, and Punjab.",
        "information_source": "ICAR - Indian Institute of Wheat and Barley Research (IIWBR)"
    },
    {
        "crop_name": "Ragi",
        "crop_category": "Cereals",
        "suitable_seasons": "Kharif, Rabi",
        "duration_min_days": 100,
        "duration_max_days": 125,
        "growing_duration_days": "100-125 days",
        "water_requirement": "Low",
        "water_requirement_mm": "350-500 mm",
        "suitable_soil": "Red soil, Light Sandy Loam, Laterite, Gravelly",
        "sowing_period": "June - July (Direct seeded/Transplanted)",
        "min_temp_c": 18.0,
        "max_temp_c": 34.0,
        "temperature_conditions": "18°C - 34°C (moderately warm climate)",
        "cultivation_notes": "Finger millet is extraordinarily calcium-rich, highly drought-resilient, and handles acidic or poor soils well.",
        "regional_information": "Karnataka (majority producer), Tamil Nadu, Uttarakhand, Maharashtra, Andhra Pradesh, and Odisha.",
        "information_source": "ICAR - Indian Institute of Millets Research (IIMR)"
    },
    {
        "crop_name": "Small millets",
        "crop_category": "Cereals",
        "suitable_seasons": "Kharif",
        "duration_min_days": 70,
        "duration_max_days": 100,
        "growing_duration_days": "70-100 days",
        "water_requirement": "Low",
        "water_requirement_mm": "250-400 mm",
        "suitable_soil": "Red, Sandy Loam, Shallow Gravelly, Laterite",
        "sowing_period": "June - July",
        "min_temp_c": 18.0,
        "max_temp_c": 36.0,
        "temperature_conditions": "18°C - 36°C (warm semi-arid conditions)",
        "cultivation_notes": "Includes Kodo, Kutki, Foxtail, and Barnyard millets. Highly resilient to erratic rain, requires minimal inputs.",
        "regional_information": "Madhya Pradesh, Chhattisgarh, Karnataka, Tamil Nadu, Andhra Pradesh, and Uttarakhand.",
        "information_source": "ICAR - Indian Institute of Millets Research"
    },
    {
        "crop_name": "Gram",
        "crop_category": "Pulses",
        "suitable_seasons": "Rabi",
        "duration_min_days": 90,
        "duration_max_days": 120,
        "growing_duration_days": "90-120 days",
        "water_requirement": "Low",
        "water_requirement_mm": "250-350 mm",
        "suitable_soil": "Black soil, Sandy Loam, Clay Loam, Alluvial",
        "sowing_period": "October - November",
        "min_temp_c": 10.0,
        "max_temp_c": 28.0,
        "temperature_conditions": "10°C - 28°C (mild, dry winter; frost-sensitive)",
        "cultivation_notes": "Chickpea / Bengal gram is India's most important rabi pulse. Fixes atmospheric nitrogen naturally; sensitive to excess moisture and frost.",
        "regional_information": "Madhya Pradesh, Rajasthan, Maharashtra, Uttar Pradesh, Karnataka, and Andhra Pradesh.",
        "information_source": "ICAR - Indian Institute of Pulses Research (IIPR), Kanpur"
    },
    {
        "crop_name": "Arhar/Tur",
        "crop_category": "Pulses",
        "suitable_seasons": "Kharif, Whole Year",
        "duration_min_days": 140,
        "duration_max_days": 190,
        "growing_duration_days": "140-190 days",
        "water_requirement": "Low",
        "water_requirement_mm": "400-600 mm",
        "suitable_soil": "Deep Black soil, Loamy, Red Sandy Loam",
        "sowing_period": "June - July",
        "min_temp_c": 18.0,
        "max_temp_c": 35.0,
        "temperature_conditions": "18°C - 35°C (warm tropical and subtropical)",
        "cultivation_notes": "Pigeonpea is a deep-rooted legume that withstands mid-season dry spells. Frequently intercropped with cotton or soybean.",
        "regional_information": "Maharashtra, Karnataka, Madhya Pradesh, Uttar Pradesh, Gujarat, and Telangana.",
        "information_source": "ICAR - Indian Institute of Pulses Research (IIPR)"
    },
    {
        "crop_name": "Moong(Green Gram)",
        "crop_category": "Pulses",
        "suitable_seasons": "Kharif, Summer, Rabi",
        "duration_min_days": 60,
        "duration_max_days": 80,
        "growing_duration_days": "60-80 days",
        "water_requirement": "Low",
        "water_requirement_mm": "300-400 mm",
        "suitable_soil": "Loamy, Sandy Loam, Alluvial, Well-drained Black soil",
        "sowing_period": "June - July (Kharif), March - April (Summer)",
        "min_temp_c": 22.0,
        "max_temp_c": 38.0,
        "temperature_conditions": "22°C - 38°C (warm humid to dry)",
        "cultivation_notes": "Short-duration catch crop ideal for crop rotation between wheat and rice. Improves soil fertility through biological nitrogen fixation.",
        "regional_information": "Rajasthan, Madhya Pradesh, Maharashtra, Karnataka, Andhra Pradesh, Gujarat, and Bihar.",
        "information_source": "ICAR - Indian Institute of Pulses Research (IIPR)"
    },
    {
        "crop_name": "Urad",
        "crop_category": "Pulses",
        "suitable_seasons": "Kharif, Summer, Rabi",
        "duration_min_days": 70,
        "duration_max_days": 90,
        "growing_duration_days": "70-90 days",
        "water_requirement": "Low",
        "water_requirement_mm": "350-450 mm",
        "suitable_soil": "Loamy, Black soil, Alluvial, Red Loam",
        "sowing_period": "June - July (Kharif), Feb - March (Summer)",
        "min_temp_c": 22.0,
        "max_temp_c": 36.0,
        "temperature_conditions": "22°C - 36°C (warm and humid)",
        "cultivation_notes": "Black gram is suitable for intercropping with sorghum, maize, and sugarcane. Tolerant of moderate shade.",
        "regional_information": "Madhya Pradesh, Uttar Pradesh, Andhra Pradesh, Tamil Nadu, Maharashtra, and Rajasthan.",
        "information_source": "ICAR - Indian Institute of Pulses Research (IIPR)"
    },
    {
        "crop_name": "Masoor",
        "crop_category": "Pulses",
        "suitable_seasons": "Rabi",
        "duration_min_days": 100,
        "duration_max_days": 130,
        "growing_duration_days": "100-130 days",
        "water_requirement": "Low",
        "water_requirement_mm": "200-300 mm",
        "suitable_soil": "Loamy, Clay, Alluvial, Black soil",
        "sowing_period": "October - November",
        "min_temp_c": 10.0,
        "max_temp_c": 26.0,
        "temperature_conditions": "10°C - 26°C (cool winter climate)",
        "cultivation_notes": "Lentil thrives under residual soil moisture after rice harvest (paira/utera cropping). Very low irrigation requirements.",
        "regional_information": "Madhya Pradesh, Uttar Pradesh, Bihar, West Bengal, and Rajasthan.",
        "information_source": "ICAR - Indian Institute of Pulses Research (IIPR)"
    },
    {
        "crop_name": "Horse-gram",
        "crop_category": "Pulses",
        "suitable_seasons": "Kharif, Rabi",
        "duration_min_days": 110,
        "duration_max_days": 135,
        "growing_duration_days": "110-135 days",
        "water_requirement": "Low",
        "water_requirement_mm": "200-350 mm",
        "suitable_soil": "Poor Shallow Red, Gravelly, Laterite, Sandy Loam",
        "sowing_period": "August - September",
        "min_temp_c": 16.0,
        "max_temp_c": 34.0,
        "temperature_conditions": "16°C - 34°C (semi-arid and dry tropical)",
        "cultivation_notes": "Extremely hardy pulse crop grown on marginal rocky drylands with negligible irrigation.",
        "regional_information": "Karnataka, Andhra Pradesh, Tamil Nadu, Odisha, and Maharashtra.",
        "information_source": "ICAR - Indian Institute of Pulses Research (IIPR)"
    },
    {
        "crop_name": "Peas & beans (Pulses)",
        "crop_category": "Pulses",
        "suitable_seasons": "Rabi",
        "duration_min_days": 80,
        "duration_max_days": 110,
        "growing_duration_days": "80-110 days",
        "water_requirement": "Medium",
        "water_requirement_mm": "350-500 mm",
        "suitable_soil": "Well-drained Loamy, Alluvial, Clay Loam",
        "sowing_period": "October - November",
        "min_temp_c": 10.0,
        "max_temp_c": 24.0,
        "temperature_conditions": "10°C - 24°C (cool, frost-free weather)",
        "cultivation_notes": "Field peas and French beans require cool conditions for flowering and pod development.",
        "regional_information": "Uttar Pradesh, Madhya Pradesh, Bihar, Punjab, and Himachal Pradesh.",
        "information_source": "ICAR - Indian Institute of Vegetable Research (IIVR), Varanasi"
    },
    {
        "crop_name": "Groundnut",
        "crop_category": "Oilseeds",
        "suitable_seasons": "Kharif, Summer, Rabi",
        "duration_min_days": 105,
        "duration_max_days": 130,
        "growing_duration_days": "105-130 days",
        "water_requirement": "Medium",
        "water_requirement_mm": "450-650 mm",
        "suitable_soil": "Sandy Loam, Red Sandy Loam, Well-drained Light Loam",
        "sowing_period": "June - July (Kharif), January - February (Summer)",
        "min_temp_c": 22.0,
        "max_temp_c": 35.0,
        "temperature_conditions": "22°C - 35°C (warm sunny weather with moderate rainfall)",
        "cultivation_notes": "Requires friable, loose, sandy loam soil to facilitate peg penetration and pod formation. Avoid heavy clays.",
        "regional_information": "Gujarat (Saurashtra), Andhra Pradesh, Tamil Nadu, Rajasthan, Karnataka, and Maharashtra.",
        "information_source": "ICAR - Directorate of Groundnut Research (DGR), Junagadh"
    },
    {
        "crop_name": "Soyabean",
        "crop_category": "Oilseeds",
        "suitable_seasons": "Kharif",
        "duration_min_days": 90,
        "duration_max_days": 110,
        "growing_duration_days": "90-110 days",
        "water_requirement": "Medium",
        "water_requirement_mm": "500-700 mm",
        "suitable_soil": "Black soil, Clay Loam, Deep fertile Loam",
        "sowing_period": "June - July",
        "min_temp_c": 20.0,
        "max_temp_c": 34.0,
        "temperature_conditions": "20°C - 34°C (warm and humid)",
        "cultivation_notes": "Major oilseed and protein source in central India. Susceptible to water stagnation; requires well-drained deep black soils.",
        "regional_information": "Madhya Pradesh (Malwa), Maharashtra (Vidarbha/Marathwada), Rajasthan, and Karnataka.",
        "information_source": "ICAR - Indian Institute of Soybean Research (IISR), Indore"
    },
    {
        "crop_name": "Rapeseed &Mustard",
        "crop_category": "Oilseeds",
        "suitable_seasons": "Rabi",
        "duration_min_days": 110,
        "duration_max_days": 140,
        "growing_duration_days": "110-140 days",
        "water_requirement": "Low",
        "water_requirement_mm": "250-400 mm",
        "suitable_soil": "Sandy Loam, Alluvial, Clay Loam",
        "sowing_period": "October - November",
        "min_temp_c": 12.0,
        "max_temp_c": 26.0,
        "temperature_conditions": "12°C - 26°C (cool and dry winter)",
        "cultivation_notes": "Leading edible oilseed of Northern India. Highly responsive to light winter irrigation; sensitive to aphid attacks if sown late.",
        "regional_information": "Rajasthan, Madhya Pradesh, Uttar Pradesh, Haryana, and West Bengal.",
        "information_source": "ICAR - Directorate of Rapeseed-Mustard Research (DRMR), Bharatpur"
    },
    {
        "crop_name": "Sesamum",
        "crop_category": "Oilseeds",
        "suitable_seasons": "Kharif, Summer",
        "duration_min_days": 75,
        "duration_max_days": 95,
        "growing_duration_days": "75-95 days",
        "water_requirement": "Low",
        "water_requirement_mm": "300-450 mm",
        "suitable_soil": "Sandy Loam, Red Loam, Alluvial",
        "sowing_period": "June - July (Kharif), Feb - March (Summer)",
        "min_temp_c": 24.0,
        "max_temp_c": 38.0,
        "temperature_conditions": "24°C - 38°C (high temperature, warm sunny)",
        "cultivation_notes": "Sesame (Til) is a drought-tolerant crop grown in light soils. Extreme heat resistance.",
        "regional_information": "West Bengal, Madhya Pradesh, Rajasthan, Uttar Pradesh, Gujarat, and Tamil Nadu.",
        "information_source": "ICAR - All India Coordinated Research Project on Sesame and Niger"
    },
    {
        "crop_name": "Sunflower",
        "crop_category": "Oilseeds",
        "suitable_seasons": "Kharif, Rabi, Summer",
        "duration_min_days": 85,
        "duration_max_days": 105,
        "growing_duration_days": "85-105 days",
        "water_requirement": "Medium",
        "water_requirement_mm": "400-600 mm",
        "suitable_soil": "Deep Black soil, Loamy, Alluvial",
        "sowing_period": "June - July (Kharif), Oct - Nov (Rabi), Jan - Feb (Summer)",
        "min_temp_c": 18.0,
        "max_temp_c": 34.0,
        "temperature_conditions": "18°C - 34°C (photo-insensitive, broad climate tolerance)",
        "cultivation_notes": "Day-neutral crop that can be cultivated year-round under irrigation. Deep root system utilizes subsoil moisture effectively.",
        "regional_information": "Karnataka, Andhra Pradesh, Maharashtra, Bihar, and Odisha.",
        "information_source": "ICAR - Indian Institute of Oilseeds Research (IIOR), Hyderabad"
    },
    {
        "crop_name": "Castor seed",
        "crop_category": "Oilseeds",
        "suitable_seasons": "Kharif, Whole Year",
        "duration_min_days": 150,
        "duration_max_days": 210,
        "growing_duration_days": "150-210 days",
        "water_requirement": "Low",
        "water_requirement_mm": "350-500 mm",
        "suitable_soil": "Sandy Loam, Red Sandy Loam, Medium Black soil",
        "sowing_period": "July - August",
        "min_temp_c": 20.0,
        "max_temp_c": 38.0,
        "temperature_conditions": "20°C - 38°C (warm, dry weather)",
        "cultivation_notes": "Highly drought-resistant industrial oilseed crop. Thrives under semi-arid conditions.",
        "regional_information": "Gujarat (leads India's production), Rajasthan, Andhra Pradesh, and Telangana.",
        "information_source": "ICAR - Indian Institute of Oilseeds Research (IIOR)"
    },
    {
        "crop_name": "Linseed",
        "crop_category": "Oilseeds",
        "suitable_seasons": "Rabi",
        "duration_min_days": 115,
        "duration_max_days": 140,
        "growing_duration_days": "115-140 days",
        "water_requirement": "Low",
        "water_requirement_mm": "250-400 mm",
        "suitable_soil": "Black soil, Alluvial, Clay Loam",
        "sowing_period": "October - November",
        "min_temp_c": 10.0,
        "max_temp_c": 25.0,
        "temperature_conditions": "10°C - 25°C (cool winter season)",
        "cultivation_notes": "Flax / Alsi grown for industrial oil and nutritional omega-3 seed. Can be grown under rain-fed conditions on moisture-retentive black soils.",
        "regional_information": "Madhya Pradesh, Uttar Pradesh, Chhattisgarh, Maharashtra, and Bihar.",
        "information_source": "ICAR - Indian Institute of Oilseeds Research (IIOR)"
    },
    {
        "crop_name": "Cotton(lint)",
        "crop_category": "Cash/Commercial Crops",
        "suitable_seasons": "Kharif",
        "duration_min_days": 150,
        "duration_max_days": 180,
        "growing_duration_days": "150-180 days",
        "water_requirement": "Medium",
        "water_requirement_mm": "650-850 mm",
        "suitable_soil": "Deep Black soil (Regur), Alluvial, Red Loam",
        "sowing_period": "April - May (North), June - July (Central and South)",
        "min_temp_c": 21.0,
        "max_temp_c": 38.0,
        "temperature_conditions": "21°C - 38°C (long frost-free growing season, warm sun)",
        "cultivation_notes": "Deep black soils with high moisture retention are optimal. Excessive rainfall during boll opening degrades lint quality.",
        "regional_information": "Gujarat, Maharashtra, Telangana, Andhra Pradesh, Rajasthan, Punjab, and Haryana.",
        "information_source": "ICAR - Central Institute for Cotton Research (CICR), Nagpur"
    },
    {
        "crop_name": "Sugarcane",
        "crop_category": "Cash/Commercial Crops",
        "suitable_seasons": "Whole Year",
        "duration_min_days": 300,
        "duration_max_days": 365,
        "growing_duration_days": "300-365 days",
        "water_requirement": "Very High",
        "water_requirement_mm": "1500-2500 mm",
        "suitable_soil": "Deep Alluvial, Heavy Loam, Deep Black soil",
        "sowing_period": "February - March (Spring) or October - November (Autumn)",
        "min_temp_c": 20.0,
        "max_temp_c": 38.0,
        "temperature_conditions": "20°C - 38°C (tropical/subtropical, warm and humid)",
        "cultivation_notes": "Long-duration cash crop requiring assured continuous irrigation (drip or furrow) and fertile deep soil.",
        "regional_information": "Uttar Pradesh, Maharashtra, Karnataka, Tamil Nadu, Bihar, and Gujarat.",
        "information_source": "ICAR - Indian Institute of Sugarcane Research (IISR), Lucknow"
    },
    {
        "crop_name": "Potato",
        "crop_category": "Vegetables",
        "suitable_seasons": "Rabi, Winter",
        "duration_min_days": 80,
        "duration_max_days": 110,
        "growing_duration_days": "80-110 days",
        "water_requirement": "Medium",
        "water_requirement_mm": "400-550 mm",
        "suitable_soil": "Sandy Loam, Alluvial, Loamy with good drainage",
        "sowing_period": "October - November",
        "min_temp_c": 12.0,
        "max_temp_c": 24.0,
        "temperature_conditions": "12°C - 24°C (tuberization requires night temps 15°C - 20°C)",
        "cultivation_notes": "Shallow-rooted tuber requiring light, porous, friable soil for tuber expansion. Very sensitive to waterlogging.",
        "regional_information": "Uttar Pradesh, West Bengal, Bihar, Gujarat, Madhya Pradesh, and Punjab.",
        "information_source": "ICAR - Central Potato Research Institute (CPRI), Shimla"
    },
    {
        "crop_name": "Onion",
        "crop_category": "Vegetables",
        "suitable_seasons": "Kharif, Rabi, Summer",
        "duration_min_days": 90,
        "duration_max_days": 120,
        "growing_duration_days": "90-120 days",
        "water_requirement": "Medium",
        "water_requirement_mm": "350-550 mm",
        "suitable_soil": "Sandy Loam, Clay Loam, Alluvial, Red Loam",
        "sowing_period": "May - June (Kharif), Oct - Nov (Rabi)",
        "min_temp_c": 13.0,
        "max_temp_c": 32.0,
        "temperature_conditions": "13°C - 32°C (moderate climate without extreme frost or heat)",
        "cultivation_notes": "Requires well-drained soils rich in humus. Water stress during bulb development leads to splitting and reduced yield.",
        "regional_information": "Maharashtra (Nashik belt), Madhya Pradesh, Karnataka, Gujarat, and Bihar.",
        "information_source": "ICAR - Directorate of Onion and Garlic Research (DOGR), Rajgurunagar"
    },
    {
        "crop_name": "Garlic",
        "crop_category": "Spices",
        "suitable_seasons": "Rabi",
        "duration_min_days": 120,
        "duration_max_days": 150,
        "growing_duration_days": "120-150 days",
        "water_requirement": "Medium",
        "water_requirement_mm": "350-500 mm",
        "suitable_soil": "Rich Sandy Loam, Loam, Alluvial",
        "sowing_period": "October - November",
        "min_temp_c": 12.0,
        "max_temp_c": 28.0,
        "temperature_conditions": "12°C - 28°C (cool vegetative growth followed by warm bulb ripening)",
        "cultivation_notes": "Requires rich friable soil with adequate organic matter and frequent light irrigations.",
        "regional_information": "Madhya Pradesh, Rajasthan, Gujarat, Uttar Pradesh, and Maharashtra.",
        "information_source": "ICAR - Directorate of Onion and Garlic Research (DOGR)"
    },
    {
        "crop_name": "Dry chillies",
        "crop_category": "Spices",
        "suitable_seasons": "Kharif, Rabi, Whole Year",
        "duration_min_days": 120,
        "duration_max_days": 160,
        "growing_duration_days": "120-160 days",
        "water_requirement": "Medium",
        "water_requirement_mm": "500-750 mm",
        "suitable_soil": "Black soil, Sandy Loam, Red Loam",
        "sowing_period": "July - August (Kharif), Oct - Nov (Rabi)",
        "min_temp_c": 18.0,
        "max_temp_c": 35.0,
        "temperature_conditions": "18°C - 35°C (warm and humid)",
        "cultivation_notes": "Essential spice crop. Water stagnation causes severe damping-off and root rot; raised-bed cultivation recommended.",
        "regional_information": "Andhra Pradesh (Guntur), Telangana, Karnataka, Madhya Pradesh, and West Bengal.",
        "information_source": "ICAR - Indian Institute of Spices Research (IISR), Kozhikode"
    },
    {
        "crop_name": "Turmeric",
        "crop_category": "Spices",
        "suitable_seasons": "Whole Year, Kharif",
        "duration_min_days": 210,
        "duration_max_days": 270,
        "growing_duration_days": "210-270 days",
        "water_requirement": "High",
        "water_requirement_mm": "1000-1400 mm",
        "suitable_soil": "Loamy, Alluvial, Red Sandy Loam",
        "sowing_period": "May - July",
        "min_temp_c": 20.0,
        "max_temp_c": 35.0,
        "temperature_conditions": "20°C - 35°C (warm humid tropical climate with partial shade tolerance)",
        "cultivation_notes": "Rhizomatous crop requiring heavy organic mulching and deep, friable, fertile loam with excellent drainage.",
        "regional_information": "Telangana, Maharashtra (Sangli/Nanded), Tamil Nadu, Andhra Pradesh, and Odisha.",
        "information_source": "ICAR - Indian Institute of Spices Research (IISR)"
    },
    {
        "crop_name": "Dry ginger",
        "crop_category": "Spices",
        "suitable_seasons": "Whole Year, Kharif",
        "duration_min_days": 220,
        "duration_max_days": 260,
        "growing_duration_days": "220-260 days",
        "water_requirement": "High",
        "water_requirement_mm": "1200-1600 mm",
        "suitable_soil": "Sandy Loam, Red Loam, Laterite with good humus",
        "sowing_period": "April - June",
        "min_temp_c": 19.0,
        "max_temp_c": 32.0,
        "temperature_conditions": "19°C - 32°C (warm and humid, sensitive to water stress)",
        "cultivation_notes": "Requires deep rich soil with excellent drainage and substantial mulching to prevent rhizome sunburn.",
        "regional_information": "Kerala, Assam, Meghalaya, Karnataka, and West Bengal.",
        "information_source": "ICAR - Indian Institute of Spices Research (IISR)"
    },
    {
        "crop_name": "Coriander",
        "crop_category": "Spices",
        "suitable_seasons": "Rabi",
        "duration_min_days": 85,
        "duration_max_days": 110,
        "growing_duration_days": "85-110 days",
        "water_requirement": "Low",
        "water_requirement_mm": "250-350 mm",
        "suitable_soil": "Well-drained Loamy, Black soil, Alluvial",
        "sowing_period": "October - November",
        "min_temp_c": 12.0,
        "max_temp_c": 28.0,
        "temperature_conditions": "12°C - 28°C (cool and dry weather during growth)",
        "cultivation_notes": "Dual-purpose spice grown for green leaves and aromatic seed. Highly sensitive to frost during flowering stage.",
        "regional_information": "Rajasthan (Kota/Baran), Madhya Pradesh, Gujarat, and Andhra Pradesh.",
        "information_source": "ICAR - National Research Centre on Seed Spices (NRCSS), Ajmer"
    },
    {
        "crop_name": "Banana",
        "crop_category": "Fruits",
        "suitable_seasons": "Whole Year",
        "duration_min_days": 330,
        "duration_max_days": 420,
        "growing_duration_days": "330-420 days",
        "water_requirement": "Very High",
        "water_requirement_mm": "1800-2400 mm",
        "suitable_soil": "Deep Fertile Loam, Clay Loam, Alluvial",
        "sowing_period": "June - July or October - November (Tissue culture suckers)",
        "min_temp_c": 15.0,
        "max_temp_c": 38.0,
        "temperature_conditions": "15°C - 38°C (warm humid tropical/subtropical)",
        "cultivation_notes": "Heavy feeder of water and organic matter. Highly rewarding with drip irrigation and fertigation management.",
        "regional_information": "Maharashtra (Jalgaon belt), Andhra Pradesh, Tamil Nadu, Gujarat, and Uttar Pradesh.",
        "information_source": "ICAR - National Research Centre for Banana (NRCB), Tiruchirappalli"
    },
    {
        "crop_name": "Sweet potato",
        "crop_category": "Vegetables",
        "suitable_seasons": "Kharif, Rabi",
        "duration_min_days": 105,
        "duration_max_days": 135,
        "growing_duration_days": "105-135 days",
        "water_requirement": "Medium",
        "water_requirement_mm": "450-600 mm",
        "suitable_soil": "Sandy Loam, Loamy, Red Loam",
        "sowing_period": "June - July (Kharif), Oct - Nov (Rabi)",
        "min_temp_c": 20.0,
        "max_temp_c": 35.0,
        "temperature_conditions": "20°C - 35°C (warm tropical climate with abundant sunshine)",
        "cultivation_notes": "Tubers develop best in well-aerated sandy loam. Intolerant of water stagnation and heavy clays.",
        "regional_information": "Odisha, West Bengal, Uttar Pradesh, Bihar, and Kerala.",
        "information_source": "ICAR - Central Tuber Crops Research Institute (CTCRI), Thiruvananthapuram"
    }
]


def generate_crop_information_csv() -> Path:
    """Generate and persist the validated crop agronomic database."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(CROP_CATALOG).to_csv(CROP_INFO_CSV_PATH, index=False)
    load_crop_catalog.cache_clear()
    _profiles_by_name.cache_clear()
    return CROP_INFO_CSV_PATH


@lru_cache(maxsize=1)
def _load_catalog_cached() -> pd.DataFrame:
    if not CROP_INFO_CSV_PATH.exists():
        generate_crop_information_csv()
    return pd.read_csv(CROP_INFO_CSV_PATH)


def load_crop_catalog() -> pd.DataFrame:
    """Load the verified crop agronomic database as a DataFrame (a fresh copy each call)."""
    return _load_catalog_cached().copy()


load_crop_catalog.cache_clear = _load_catalog_cached.cache_clear  # type: ignore[attr-defined]


@lru_cache(maxsize=1)
def _profiles_by_name() -> Dict[str, Dict]:
    """Case-insensitive index of crop profiles keyed by lower-cased crop name."""
    return {
        str(rec["crop_name"]).lower(): rec
        for rec in _load_catalog_cached().to_dict(orient="records")
    }


def get_crop_profile(crop_name: str) -> Optional[Dict]:
    """Retrieve the full agronomic profile for a crop (exact match, then substring match)."""
    key = str(crop_name).strip().lower()
    if not key:
        return None
    profiles = _profiles_by_name()
    if key in profiles:
        return dict(profiles[key])
    for name, rec in profiles.items():
        if key in name:
            return dict(rec)
    return None


_SEASON_ALIASES = {"autumn": "kharif", "winter": "rabi", "zaid": "summer"}


def parse_seasons(seasons: str) -> List[str]:
    """Splits a comma-separated season string into canonical lower-case season names."""
    tokens = [t.strip().lower() for t in str(seasons or "").split(",") if t.strip()]
    return [_SEASON_ALIASES.get(t, t) for t in tokens]


def is_suitable_for_season(profile: Dict, season: str) -> bool:
    """
    True when a crop can be grown in the requested season. Crops with no season data and
    perennial 'Whole Year' crops are treated as eligible in every season.
    """
    allowed = parse_seasons(profile.get("suitable_seasons", ""))
    if not allowed or "whole year" in allowed:
        return True
    wanted = _SEASON_ALIASES.get(str(season).strip().lower(), str(season).strip().lower())
    return wanted == "whole year" or wanted in allowed


def get_crop_categories() -> List[str]:
    """List available unique crop categories."""
    df = load_crop_catalog()
    return sorted(df["crop_category"].unique().tolist())


def filter_crops(
    category: Optional[str] = None,
    season: Optional[str] = None,
    water_req: Optional[str] = None,
    max_duration: Optional[int] = None
) -> pd.DataFrame:
    """Filter crops by category, season, water requirements, and duration."""
    df = load_crop_catalog()
    if category and category != "All":
        df = df[df["crop_category"] == category]
    if season and season != "All":
        df = df[df["suitable_seasons"].str.contains(season, case=False, na=False, regex=False)]
    if water_req and water_req != "All":
        df = df[df["water_requirement"] == water_req]
    if max_duration:
        df = df[df["duration_max_days"] <= max_duration]
    return df


if __name__ == "__main__":
    path = generate_crop_information_csv()
    print(f"Generated verified crop agronomic database at: {path} with {len(CROP_CATALOG)} crops.")
