import os
import io
import base64
import qrcode
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class SocialSharingService:
    def __init__(self):
        self.brand_colors = {
            "primary": "#10B981",  # EarnAura Green
            "secondary": "#059669", 
            "accent": "#F59E0B",   # Gold for achievements
            "text_primary": "#1F2937",
            "text_secondary": "#6B7280",
            "background": "#F9FAFB"
        }
        
        # Create uploads directory if it doesn't exist
        self.upload_dir = "/app/backend/uploads/achievements"
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def generate_achievement_image(self, 
                                  achievement_type: str,
                                  milestone_text: str, 
                                  amount: float = None,
                                  user_name: str = "User",
                                  badge_info: Dict[str, Any] = None) -> str:
        """Generate branded achievement image for social sharing"""
        
        # Create image canvas
        width, height = 1080, 1080  # Instagram Story size
        img = Image.new('RGB', (width, height), self.brand_colors["background"])
        draw = ImageDraw.Draw(img)
        
        try:
            # Try to load fonts (fallback to default if not available)
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVu-Sans-Bold.ttf", 60)
                subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVu-Sans.ttf", 40)
                amount_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVu-Sans-Bold.ttf", 80)
                small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVu-Sans.ttf", 30)
            except:
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
                amount_font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # Background gradient effect (simplified with rectangles)
            for i in range(0, height, 20):
                alpha = int(255 * (1 - i / height) * 0.1)
                color = self._hex_to_rgb(self.brand_colors["primary"]) + (alpha,)
                overlay = Image.new('RGBA', (width, height), color)
                img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
            
            # Draw EarnAura logo/branding at top
            self._draw_centered_text(draw, "EarnAura", title_font, 
                                   width // 2, 150, self.brand_colors["primary"])
            
            # Draw achievement badge/icon
            badge_y = 280
            if badge_info:
                badge_icon = badge_info.get('icon', '🏆')
                self._draw_centered_text(draw, badge_icon, amount_font,
                                       width // 2, badge_y, self.brand_colors["accent"])
            
            # Draw achievement title
            achievement_title = self._get_achievement_title(achievement_type)
            self._draw_centered_text(draw, achievement_title, subtitle_font,
                                   width // 2, badge_y + 120, self.brand_colors["text_primary"])
            
            # Draw milestone text
            self._draw_wrapped_text(draw, milestone_text, subtitle_font,
                                  width // 2, badge_y + 200, width - 100, 
                                  self.brand_colors["text_secondary"])
            
            # Draw amount if provided
            if amount:
                amount_text = f"₹{self._format_amount(amount)}"
                self._draw_centered_text(draw, amount_text, amount_font,
                                       width // 2, badge_y + 320, self.brand_colors["accent"])
            
            # Draw user name
            self._draw_centered_text(draw, f"- {user_name}", small_font,
                                   width // 2, height - 250, self.brand_colors["text_secondary"])
            
            # Draw motivational message
            motivational_msg = self._get_motivational_message(achievement_type)
            self._draw_centered_text(draw, motivational_msg, small_font,
                                   width // 2, height - 180, self.brand_colors["primary"])
            
            # Draw app branding at bottom
            self._draw_centered_text(draw, "Track your finances with EarnAura", small_font,
                                   width // 2, height - 100, self.brand_colors["text_secondary"])
            
            # Save image
            timestamp = int(datetime.now().timestamp())
            filename = f"achievement_{achievement_type}_{timestamp}.jpg"
            filepath = os.path.join(self.upload_dir, filename)
            img.save(filepath, "JPEG", quality=95)
            
            return filename
            
        except Exception as e:
            logger.error(f"Error generating achievement image: {e}")
            return None
    
    def generate_milestone_celebration_image(self, 
                                           milestone_type: str,
                                           achievement_text: str,
                                           stats: Dict[str, Any],
                                           user_name: str = "User") -> str:
        """Generate milestone celebration posts"""
        
        # Create celebration image
        width, height = 1200, 630  # Facebook/WhatsApp optimal size
        img = Image.new('RGB', (width, height), self.brand_colors["background"])
        draw = ImageDraw.Draw(img)
        
        try:
            # Load fonts
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVu-Sans-Bold.ttf", 50)
                subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVu-Sans.ttf", 32)
                stats_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVu-Sans-Bold.ttf", 40)
            except:
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
                stats_font = ImageFont.load_default()
            
            # Celebration background
            celebration_emoji = "🎉" if milestone_type == "savings" else "🔥" if milestone_type == "streak" else "🏆"
            
            # Draw celebration elements
            self._draw_centered_text(draw, celebration_emoji * 5, title_font,
                                   width // 2, 80, self.brand_colors["accent"])
            
            self._draw_centered_text(draw, "MILESTONE ACHIEVED!", title_font,
                                   width // 2, 160, self.brand_colors["primary"])
            
            # Draw achievement text
            self._draw_wrapped_text(draw, achievement_text, subtitle_font,
                                  width // 2, 240, width - 100, self.brand_colors["text_primary"])
            
            # Draw key stats
            y_offset = 350
            for key, value in stats.items():
                stat_text = f"{key.replace('_', ' ').title()}: {value}"
                self._draw_centered_text(draw, stat_text, stats_font,
                                       width // 2, y_offset, self.brand_colors["text_secondary"])
                y_offset += 50
            
            # EarnAura branding
            self._draw_centered_text(draw, "EarnAura - Smart Finance Tracking", subtitle_font,
                                   width // 2, height - 60, self.brand_colors["primary"])
            
            # Save image
            timestamp = int(datetime.now().timestamp())
            filename = f"milestone_{milestone_type}_{timestamp}.jpg"
            filepath = os.path.join(self.upload_dir, filename)
            img.save(filepath, "JPEG", quality=95)
            
            return filename
            
        except Exception as e:
            logger.error(f"Error generating milestone image: {e}")
            return None
    
    def generate_social_share_content(self, 
                                    platform: str,
                                    achievement_type: str,
                                    milestone_text: str,
                                    image_filename: str,
                                    user_name: str = "User") -> Dict[str, Any]:
        """Generate platform-specific share content"""
        
        image_url = f"/uploads/achievements/{image_filename}"
        
        base_text = f"{milestone_text} 💪\n\nTracking my finances with EarnAura! 📱💰"
        
        if platform == "instagram":
            return {
                "story_text": base_text + "\n\n#EarnAura #FinanceGoals #StudentFinance #MoneyManagement",
                "image_url": image_url,
                "action_text": "Copy text and share on Instagram Stories",
                "instructions": "1. Copy this text\n2. Open Instagram\n3. Create new story\n4. Add this image\n5. Paste the text as caption"
            }
        
        elif platform == "whatsapp":
            whatsapp_text = base_text.replace('\n\n', '%0A%0A').replace('\n', '%0A')
            return {
                "share_url": f"https://wa.me/?text={whatsapp_text}",
                "image_url": image_url,
                "text": base_text,
                "action_text": "Share on WhatsApp Status"
            }
        
        else:
            return {
                "text": base_text,
                "image_url": image_url
            }
    
    def _draw_centered_text(self, draw, text, font, x, y, color):
        """Draw centered text"""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        draw.text((x - text_width // 2, y - text_height // 2), text, 
                 font=font, fill=color)
    
    def _draw_wrapped_text(self, draw, text, font, x, y, max_width, color):
        """Draw text with word wrapping"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        line_height = 40
        start_y = y - (len(lines) * line_height) // 2
        
        for i, line in enumerate(lines):
            self._draw_centered_text(draw, line, font, x, start_y + i * line_height, color)
    
    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _format_amount(self, amount):
        """Format amount for display"""
        if amount >= 100000:
            return f"{amount/100000:.1f}L"
        elif amount >= 1000:
            return f"{amount/1000:.1f}K"
        else:
            return f"{amount:.0f}"
    
    def _get_achievement_title(self, achievement_type):
        """Get title for achievement type"""
        titles = {
            "savings_milestone": "Savings Milestone",
            "streak_achievement": "Streak Achievement", 
            "budget_success": "Budget Master",
            "goal_completed": "Goal Achieved",
            "hustle_success": "Hustle Hero",
            "badge_earned": "Badge Earned"
        }
        return titles.get(achievement_type, "Achievement Unlocked")
    
    def _get_motivational_message(self, achievement_type):
        """Get motivational message for achievement type"""
        messages = {
            "savings_milestone": "Every rupee saved is a step toward financial freedom! 💪",
            "streak_achievement": "Consistency is the key to success! Keep going! 🔥",
            "budget_success": "Smart budgeting leads to smart savings! 📊",
            "goal_completed": "Dreams become reality with dedication! 🎯",
            "hustle_success": "Your side hustle is paying off! 💼",
            "badge_earned": "Excellence recognized! You're crushing it! 🏆"
        }
        return messages.get(achievement_type, "Keep building your financial future!")

# Global instance
_social_sharing_service = None

async def get_social_sharing_service():
    """Get social sharing service instance"""
    global _social_sharing_service
    if _social_sharing_service is None:
        _social_sharing_service = SocialSharingService()
    return _social_sharing_service
