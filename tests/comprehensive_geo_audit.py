#!/usr/bin/env python3
"""
בדיקת מהימנות נתונים גיאוגרפיים - TennisMatchUp
סקריפט בדיקה מעמיק לזיהוי בעיות ברכיבי הגיאוגרפיה
"""

import os
import sys
from dotenv import load_dotenv

# הוסף את הנתיב הנוכחי ל-PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

load_dotenv()

def run_geographic_audit():
    """הרצת בדיקה מקיפה של נתוני הגיאוגרפיה"""
    
    print("🏥 TennisMatchUp - בדיקת מהימנות נתונים גיאוגרפיים")
    print("=" * 70)
    
    try:
        from app import create_app
        from models.database import db
        from models.player import Player
        from models.court import Court
        from models.user import User
        from services.geo_service import GeoService
        
        app = create_app()
        
        with app.app_context():
            
            # ========== שלב 1: סקירת נתונים כללית ==========
            print("📊 שלב 1: סקירת נתונים כללית")
            print("-" * 40)
            
            total_users = User.query.count()
            total_players = Player.query.count()
            total_courts = Court.query.filter(Court.is_active == True).count()
            
            print(f"📈 סה\"כ משתמשים: {total_users}")
            print(f"🎾 סה\"כ שחקנים: {total_players}")
            print(f"🏟️  סה\"כ מגרשים פעילים: {total_courts}")
            
            if total_players == 0 or total_courts == 0:
                print("❌ אין נתונים מספיקים בדטהבייס לבדיקה")
                return False
            
            # ========== שלב 2: בדיקת קואורדינטות ==========
            print("\\n🌍 שלב 2: ניתוח קואורדינטות")
            print("-" * 40)
            
            # בדיקת שחקנים
            players_with_coords = Player.query.filter(
                Player.latitude.isnot(None),
                Player.longitude.isnot(None)
            ).count()
            
            players_with_location_text = Player.query.filter(
                Player.preferred_location.isnot(None),
                Player.preferred_location != ''
            ).count()
            
            player_coord_percentage = (players_with_coords/total_players*100) if total_players > 0 else 0
            print(f"🎯 שחקנים עם קואורדינטות: {players_with_coords}/{total_players} ({player_coord_percentage:.1f}%)")
            print(f"📍 שחקנים עם טקסט מיקום: {players_with_location_text}/{total_players}")
            
            # בדיקת מגרשים
            courts_with_coords = Court.query.filter(
                Court.is_active == True,
                Court.latitude.isnot(None),
                Court.longitude.isnot(None)
            ).count()
            
            courts_with_location_text = Court.query.filter(
                Court.is_active == True,
                Court.location.isnot(None),
                Court.location != ''
            ).count()
            
            court_coord_percentage = (courts_with_coords/total_courts*100) if total_courts > 0 else 0
            print(f"🎯 מגרשים עם קואורדינטות: {courts_with_coords}/{total_courts} ({court_coord_percentage:.1f}%)")
            print(f"📍 מגרשים עם טקסט מיקום: {courts_with_location_text}/{total_courts}")
            
            # ========== שלב 3: דוגמיות של נתונים ==========
            print("\\n🔍 שלב 3: דוגמיות נתונים")
            print("-" * 40)
            
            print("\\n🎾 דוגמיות שחקנים:")
            sample_players = Player.query.join(User).limit(5).all()
            for i, player in enumerate(sample_players, 1):
                coords_status = "✅" if (player.latitude and player.longitude) else "❌"
                print(f"  {i}. {player.user.full_name}")
                print(f"     מיקום רצוי: '{player.preferred_location or 'לא מוגדר'}'")
                print(f"     קואורדינטות: {coords_status} ({player.latitude}, {player.longitude})")
            
            print("\\n🏟️  דוגמיות מגרשים:")
            sample_courts = Court.query.filter(Court.is_active == True).limit(5).all()
            for i, court in enumerate(sample_courts, 1):
                coords_status = "✅" if (court.latitude and court.longitude) else "❌"
                print(f"  {i}. {court.name}")
                print(f"     מיקום: '{court.location}'")
                print(f"     קואורדינטות: {coords_status} ({court.latitude}, {court.longitude})")
            
            # ========== שלב 4: בדיקת מטמון GeoService ==========
            print("\\n💾 שלב 4: בדיקת מטמון GeoService")
            print("-" * 40)
            
            cache_size = len(GeoService._location_cache)
            print(f"📦 גודל מטמון: {cache_size} מיקומים")
            
            if cache_size > 0:
                print("🔍 תוכן המטמון (10 הראשונים):")
                for i, (location, coords) in enumerate(list(GeoService._location_cache.items())[:10]):
                    print(f"   {i+1}. '{location}' → {coords}")
                    
                    # בדיקת קואורדינטות חשודות
                    if coords and len(coords) == 2:
                        lat, lng = coords
                        # ישראל צריכה להיות בטווח בערך: lat 29-34, lng 34-36
                        if not (29 <= lat <= 34 and 34 <= lng <= 36):
                            print(f"      ⚠️  קואורדינטות חשודות - מחוץ לישראל!")
            
            # ========== שלב 5: בדיקת API ==========
            print("\\n🌐 שלב 5: בדיקת GeoService API")
            print("-" * 40)
            
            api_key_exists = bool(GeoService.API_KEY)
            print(f"🔑 מפתח API קיים: {'✅ כן' if api_key_exists else '❌ לא'}")
            
            if api_key_exists:
                print("🧪 בדיקת API עם מיקומים ידועים...")
                
                test_locations = [
                    ("Tel Aviv", (32.0853, 34.7818)),     # קואורדינטות נכונות ידועות
                    ("Jerusalem", (31.7683, 35.2137)),    # קואורדינטות נכונות ידועות
                    ("Haifa", (32.7940, 34.9896)),        # קואורדינטות נכונות ידועות
                    ("Rishon LeZion", (31.9730, 34.8070)) # קואורדינטות נכונות ידועות
                ]
                
                api_working = True
                suspicious_results = []
                
                for location, expected_coords in test_locations:
                    try:
                        coords = GeoService.get_coordinates(location)
                        if coords:
                            # חישוב מרחק מהקואורדינטות הצפויות
                            distance = GeoService.calculate_distance_km(coords, expected_coords)
                            
                            print(f"  📍 {location}:")
                            print(f"     קיבלנו: {coords[0]:.4f}, {coords[1]:.4f}")
                            print(f"     צפוי: {expected_coords[0]:.4f}, {expected_coords[1]:.4f}")
                            print(f"     מרחק מהצפוי: {distance:.2f} ק\"מ")
                            
                            if distance > 5:  # אם המרחק גדול מ-5 ק"מ
                                print(f"     ⚠️  מרחק חשוד - יותר מ-5 ק\"מ מהמיקום הצפוי!")
                                suspicious_results.append((location, coords, expected_coords, distance))
                            else:
                                print(f"     ✅ קואורדינטות נראות נכונות")
                        else:
                            print(f"  ❌ {location}: לא נמצאו קואורדינטות")
                            api_working = False
                    except Exception as e:
                        print(f"  ❌ {location}: שגיאה - {str(e)}")
                        api_working = False
                
                if suspicious_results:
                    print("\\n🚨 תוצאות חשודות שנמצאו:")
                    for location, received, expected, distance in suspicious_results:
                        print(f"   {location}: סטיה של {distance:.2f} ק\"מ")
                
                if not api_working:
                    print("⚠️  יש בעיות עם ה-API - זה עלול להשפיע על דיוק ההמלצות")
            else:
                print("❌ אין מפתח API - לא ניתן לבדוק את שירות הגיאוגרפיה")
            
            # ========== שלב 6: בדיקת מיקומים ספציפיים בדטהבייס ==========
            print("\\n🔍 שלב 6: בדיקת מיקומים ספציפיים")
            print("-" * 40)
            
            # בדיקת מגרשים בערים הגדולות
            major_cities = ['jerusalem', 'tel aviv', 'haifa', 'beer sheva']
            
            for city in major_cities:
                city_courts = Court.query.filter(
                    Court.is_active == True,
                    Court.location.ilike(f'%{city}%')
                ).all()
                
                if city_courts:
                    print(f"\\n🏟️  מגרשים ב{city.title()}:")
                    for court in city_courts[:3]:  # הצג עד 3 מגרשים
                        print(f"     {court.name}")
                        print(f"     מיקום: {court.location}")
                        if court.latitude and court.longitude:
                            print(f"     קואורדינטות: {court.latitude:.4f}, {court.longitude:.4f}")
                            
                            # בדיקת קואורדינטות ירושלים ספציפית
                            if 'jerusalem' in city and court.latitude and court.longitude:
                                expected_jerusalem = (31.7683, 35.2137)
                                distance_from_center = GeoService.calculate_distance_km(
                                    (court.latitude, court.longitude),
                                    expected_jerusalem
                                )
                                print(f"     מרחק ממרכז ירושלים: {distance_from_center:.2f} ק\"מ")
                                
                                if distance_from_center > 50:  # יותר מ-50 ק"מ מירושלים
                                    print(f"     🚨 בעיה חמורה: המגרש רחוק מידי מירושלים!")
                        else:
                            print(f"     ❌ אין קואורדינטות")
            
            # ========== שלב 7: בדיקת אלגוריתם המלצות ==========
            print("\\n🧠 שלב 7: בדיקת אלגוריתם ההמלצות")
            print("-" * 40)
            
            # נבחר שני שחקנים עם קואורדינטות לבדיקה
            test_players = Player.query.filter(
                Player.latitude.isnot(None),
                Player.longitude.isnot(None)
            ).limit(2).all()
            
            if len(test_players) >= 2:
                p1, p2 = test_players[0], test_players[1]
                print(f"🎯 בדיקת זוג שחקנים:")
                print(f"   שחקן 1: {p1.user.full_name} ({p1.preferred_location})")
                print(f"   קואורדינטות: {p1.latitude:.4f}, {p1.longitude:.4f}")
                print(f"   שחקן 2: {p2.user.full_name} ({p2.preferred_location})")
                print(f"   קואורדינטות: {p2.latitude:.4f}, {p2.longitude:.4f}")
                
                # חישוב מרחק בין השחקנים
                distance_between_players = GeoService.calculate_distance_km(
                    (p1.latitude, p1.longitude),
                    (p2.latitude, p2.longitude)
                )
                print(f"   מרחק בין השחקנים: {distance_between_players:.2f} ק\"מ")
                
                # בדיקת הצעת מגרשים
                try:
                    print("\\n🏟️  מריץ אלגוריתם המלצת מגרשים...")
                    meeting_points = GeoService.suggest_meeting_points(
                        (p1.latitude, p1.longitude),
                        (p2.latitude, p2.longitude),
                        max_courts=10
                    )
                    
                    if meeting_points:
                        print(f"   נמצאו {len(meeting_points)} מגרשים מתאימים:")
                        
                        problem_found = False
                        for i, suggestion in enumerate(meeting_points, 1):
                            court = suggestion['court']
                            dist_p1 = suggestion['distance_to_player1']
                            dist_p2 = suggestion['distance_to_player2']
                            score = suggestion['total_score']
                            
                            print(f"     {i}. {court.name} ({court.location})")
                            print(f"        מרחק לשחקן 1: {dist_p1:.1f}ק\"מ")
                            print(f"        מרחק לשחקן 2: {dist_p2:.1f}ק\"מ")
                            print(f"        ציון כולל: {score:.1f}")
                            
                            # זיהוי הבעיה הספציפית שאתה ציינת
                            # אם ירושלים מופיעה במקום גבוה בזמן שהשחקנים קרובים זה לזה
                            if ('jerusalem' in court.location.lower() and 
                                distance_between_players < 20 and  # שחקנים קרובים (פחות מ-20 ק"מ)
                                i <= 3):  # מופיע ב-3 הראשונים
                                
                                print(f"        🚨 בעיה זוהתה! מגרש בירושלים מופיע במקום {i}")
                                print(f"           בזמן ששני השחקנים רחוקים רק {distance_between_players:.1f}ק\"מ זה מזה")
                                print(f"           זה לא הגיוני שירושלים תהיה האופציה הטובה ביותר")
                                problem_found = True
                            
                            # בדיקה נוספת: מרחקים לא הגיוניים
                            if dist_p1 > 50 or dist_p2 > 50:
                                print(f"        ⚠️  מרחקים גדולים מידי למגרש מומלץ")
                        
                        if problem_found:
                            print("\\n🎯 בעיה אותרה באלגוריתם ההמלצות!")
                            print("   הסיבות האפשריות:")
                            print("   1. קואורדינטות שגויות של מגרשים בירושלים")
                            print("   2. בעיה באלגוריתם חישוב הניקוד")
                            print("   3. נתונים שגויים במטמון הגיאוגרפי")
                        else:
                            print("\\n✅ האלגוריתם נראה תקין עבור הדוגמא הזו")
                            
                    else:
                        print("   ❌ לא נמצאו מגרשים מתאימים")
                        
                except Exception as e:
                    print(f"   ❌ שגיאה באלגוריתם ההמלצות: {str(e)}")
                    import traceback
                    traceback.print_exc()
            else:
                print("❌ אין מספיק שחקנים עם קואורדינטות לבדיקת האלגוריתם")
            
            # ========== שלב 8: סיכום ותוצאות ==========
            print("\\n📋 סיכום ותוצאות")
            print("=" * 70)
            
            issues_found = []
            recommendations = []
            
            # זיהוי בעיות
            if player_coord_percentage < 80:
                issues_found.append(f"רק {player_coord_percentage:.1f}% מהשחקנים יש להם קואורדינטות")
                recommendations.append("עדכן קואורדינטות שחקנים: GeoService.batch_update_all_players()")
            
            if court_coord_percentage < 80:
                issues_found.append(f"רק {court_coord_percentage:.1f}% מהמגרשים יש להם קואורדינטות")
                recommendations.append("עדכן קואורדינטות מגרשים דרך owner interface")
            
            if not api_key_exists:
                issues_found.append("אין מפתח API לשירות הגיאוגרפיה")
                recommendations.append("הוסף OPENCAGE_API_KEY לקובץ .env")
            
            if cache_size > 20:
                issues_found.append(f"מטמון גדול ({cache_size} מיקומים) - ייתכן שיש נתונים שגויים")
                recommendations.append("נקה מטמון: GeoService._location_cache.clear()")
            
            # הצגת התוצאות
            if not issues_found:
                print("✅ לא נמצאו בעיות משמעותיות בנתוני הגיאוגרפיה")
                print("🔍 אם עדיין יש בעיות בהמלצות, הבעיה כנראה באלגוריתם עצמו")
            else:
                print("🚨 נמצאו הבעיות הבאות:")
                for i, issue in enumerate(issues_found, 1):
                    print(f"   {i}. {issue}")
            
            if recommendations:
                print("\\n🎯 המלצות לפעולה:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"   {i}. {rec}")
            
            print("\\n📞 פעולות בדיקה נוספות:")
            print("   • בדוק לוגים של בקשות לשירות הגיאוגרפיה")
            print("   • הרץ בדיקת המלצות עם דוגמיות ידועות")
            print("   • השווה תוצאות לפני ואחרי ניקוי מטמון")
            print("   • בדוק ביצועים של חישובי מרחק")
            
            print("\\n" + "=" * 70)
            print("🏁 בדיקה הושלמה!")
            
            return len(issues_found) == 0  # החזר True אם לא נמצאו בעיות
            
    except Exception as e:
        print(f"❌ שגיאה בבדיקה: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def quick_fix_suggestions():
    """הצעות תיקון מהיר"""
    print("\\n🔧 הצעות תיקון מהיר:")
    print("=" * 50)
    
    print("1. 🧹 נקה מטמון גיאוגרפי:")
    print("   from services.geo_service import GeoService")
    print("   GeoService._location_cache.clear()")
    
    print("\\n2. 🔄 עדכן קואורדינטות ירושלים:")
    print("   coords = GeoService.get_coordinates('Jerusalem')")
    print("   print(f'Jerusalem coords: {coords}')")
    
    print("\\n3. 🧪 בדוק מגרש ספציפי:")
    print("   from models.court import Court")
    print("   court = Court.query.filter(Court.location.ilike('%jerusalem%')).first()")
    print("   if court: print(f'{court.name}: {court.latitude}, {court.longitude}')")
    
    print("\\n4. 📊 הרץ בדיקת אלגוריתם:")
    print("   from services.court_recommendation_engine import CourtRecommendationEngine")
    print("   courts = CourtRecommendationEngine.find_recommended_courts(player_id=1, sort_by='distance', limit=10)")
    print("   for result in courts[:5]: print(f'{result[\"court\"].name}: {result[\"distance_km\"]}km')")

if __name__ == "__main__":
    print("🚀 מתחיל בדיקה...")
    success = run_geographic_audit()
    
    if not success:
        print("\\n💡 רוצה הצעות תיקון מהיר?")
        quick_fix_suggestions()
    
    sys.exit(0 if success else 1)