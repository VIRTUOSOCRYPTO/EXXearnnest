import os
import io
import uuid
import base64
import logging
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from database import get_database
import shutil

logger = logging.getLogger(__name__)

class EnhancedPhotoService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        
        # Brand colors for EarnNest
        self.brand_colors = {
            "primary": "#10B981",      # EarnNest Green
            "secondary": "#059669", 
            "accent": "#F59E0B",       # Gold for achievements
            "purple": "#8B5CF6",       # Purple for milestones
            "blue": "#3B82F6",         # Blue for goals
            "text_primary": "#1F2937",
            "text_secondary": "#6B7280",
            "background": "#F9FAFB",
            "white": "#FFFFFF"
        }
        
        # Create directories
        self.upload_dir = "/app/backend/uploads"
        self.achievement_dir = f"{self.upload_dir}/achievements"
        self.custom_photos_dir = f"{self.upload_dir}/custom_photos"
        
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.achievement_dir, exist_ok=True)
        os.makedirs(self.custom_photos_dir, exist_ok=True)

    async def upload_custom_achievement_photo(self, user_id: str, achievement_id: str, 
                                            file_content: bytes, filename: str) -> Dict[str, Any]:
        """Upload custom photo for achievement"""
        try:
            # Validate file type
            if not self._is_valid_image_file(filename):
                return {"success": False, "message": "Invalid image file type"}
            
            # Generate unique filename
            file_extension = filename.split('.')[-1].lower()
            custom_filename = f"custom_{user_id}_{achievement_id}_{int(datetime.now(timezone.utc).timestamp())}.{file_extension}"
            file_path = f"{self.custom_photos_dir}/{custom_filename}"
            
            # Save original file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Process and optimize image
            processed_path = await self._process_uploaded_image(file_path)
            
            # Create database record
            photo_doc = {
                "id": f"photo_{user_id}_{achievement_id}_{int(datetime.now(timezone.utc).timestamp())}",
                "user_id": user_id,
                "achievement_id": achievement_id,
                "achievement_type": "custom",
                "photo_type": "custom",
                "original_photo_url": f"/uploads/custom_photos/{custom_filename}",
                "final_photo_url": processed_path,
                "photo_metadata": {
                    "original_filename": filename,
                    "file_size": len(file_content),
                    "processed_at": datetime.now(timezone.utc).isoformat()
                },
                "privacy_level": "public",
                "status": "active",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            await self.db.achievement_photos.insert_one(photo_doc)
            
            return {
                "success": True,
                "photo_id": photo_doc["id"],
                "photo_url": processed_path,
                "message": "Photo uploaded successfully"
            }
            
        except Exception as e:
            logger.error(f"Upload custom achievement photo error: {str(e)}")
            return {"success": False, "message": "Failed to upload photo"}

    async def generate_branded_achievement_photo(self, user_id: str, achievement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate branded achievement photo with templates"""
        try:
            achievement_type = achievement_data.get("achievement_type", "milestone")
            template_style = achievement_data.get("template_style", "modern")
            
            # Generate the branded image
            if achievement_type == "milestone":
                image_path = await self._generate_milestone_template(user_id, achievement_data, template_style)
            elif achievement_type == "badge":
                image_path = await self._generate_badge_template(user_id, achievement_data, template_style)
            elif achievement_type == "goal_completion":
                image_path = await self._generate_goal_template(user_id, achievement_data, template_style)
            elif achievement_type == "streak":
                image_path = await self._generate_streak_template(user_id, achievement_data, template_style)
            else:
                image_path = await self._generate_generic_template(user_id, achievement_data, template_style)
            
            # Create database record
            photo_doc = {
                "id": f"branded_{user_id}_{achievement_data.get('achievement_id', 'unknown')}_{int(datetime.now(timezone.utc).timestamp())}",
                "user_id": user_id,
                "achievement_id": achievement_data.get("achievement_id"),
                "achievement_type": achievement_type,
                "photo_type": "branded_template",
                "branded_photo_url": image_path,
                "final_photo_url": image_path,
                "photo_metadata": {
                    "template_style": template_style,
                    "achievement_data": achievement_data,
                    "generated_at": datetime.now(timezone.utc).isoformat()
                },
                "privacy_level": "public",
                "status": "active",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            await self.db.achievement_photos.insert_one(photo_doc)
            
            return {
                "success": True,
                "photo_id": photo_doc["id"],
                "photo_url": image_path,
                "message": "Branded photo generated successfully"
            }
            
        except Exception as e:
            logger.error(f"Generate branded achievement photo error: {str(e)}")
            return {"success": False, "message": "Failed to generate branded photo"}

    async def create_combined_achievement_photo(self, user_id: str, custom_photo_path: str, 
                                              achievement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Combine custom photo with branded overlay"""
        try:
            # Load custom photo
            custom_image = Image.open(custom_photo_path)
            
            # Create branded overlay
            overlay = await self._create_achievement_overlay(achievement_data)
            
            # Combine images
            combined_image = await self._combine_photo_with_overlay(custom_image, overlay)
            
            # Save combined image
            filename = f"combined_{user_id}_{achievement_data.get('achievement_id')}_{int(datetime.now(timezone.utc).timestamp())}.jpg"
            file_path = f"{self.achievement_dir}/{filename}"
            combined_image.save(file_path, "JPEG", quality=90, optimize=True)
            
            # Create database record
            photo_doc = {
                "id": f"combined_{user_id}_{achievement_data.get('achievement_id')}_{int(datetime.now(timezone.utc).timestamp())}",
                "user_id": user_id,
                "achievement_id": achievement_data.get("achievement_id"),
                "achievement_type": achievement_data.get("achievement_type", "milestone"),
                "photo_type": "combined",
                "original_photo_url": custom_photo_path,
                "final_photo_url": f"/uploads/achievements/{filename}",
                "photo_metadata": {
                    "combination_method": "overlay",
                    "achievement_data": achievement_data,
                    "processed_at": datetime.now(timezone.utc).isoformat()
                },
                "privacy_level": "public",
                "status": "active",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            await self.db.achievement_photos.insert_one(photo_doc)
            
            return {
                "success": True,
                "photo_id": photo_doc["id"],
                "photo_url": f"/uploads/achievements/{filename}",
                "message": "Combined photo created successfully"
            }
            
        except Exception as e:
            logger.error(f"Create combined achievement photo error: {str(e)}")
            return {"success": False, "message": "Failed to create combined photo"}

    async def get_user_achievement_photos(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's achievement photos"""
        try:
            photos = await self.db.achievement_photos.find({
                "user_id": user_id,
                "status": "active"
            }).sort("created_at", -1).limit(limit).to_list(None)
            
            # Enrich with like counts and recent reactions
            for photo in photos:
                photo["like_count"] = await self.db.photo_likes.count_documents({"photo_id": photo["id"]})
                photo["user_liked"] = await self.db.photo_likes.find_one({
                    "photo_id": photo["id"],
                    "user_id": user_id
                }) is not None
            
            return photos
            
        except Exception as e:
            logger.error(f"Get user achievement photos error: {str(e)}")
            return []

    async def like_achievement_photo(self, user_id: str, photo_id: str) -> Dict[str, Any]:
        """Like or unlike an achievement photo"""
        try:
            # Check if already liked
            existing_like = await self.db.photo_likes.find_one({
                "user_id": user_id,
                "photo_id": photo_id
            })
            
            if existing_like:
                # Unlike
                await self.db.photo_likes.delete_one({"_id": existing_like["_id"]})
                await self.db.achievement_photos.update_one(
                    {"id": photo_id},
                    {"$inc": {"like_count": -1}}
                )
                return {"success": True, "action": "unliked", "liked": False}
            else:
                # Like
                like_doc = {
                    "id": f"like_{user_id}_{photo_id}_{int(datetime.now(timezone.utc).timestamp())}",
                    "user_id": user_id,
                    "photo_id": photo_id,
                    "created_at": datetime.now(timezone.utc)
                }
                
                await self.db.photo_likes.insert_one(like_doc)
                await self.db.achievement_photos.update_one(
                    {"id": photo_id},
                    {"$inc": {"like_count": 1}}
                )
                
                # Notify photo owner
                photo = await self.db.achievement_photos.find_one({"id": photo_id})
                if photo and photo["user_id"] != user_id:
                    await self._notify_photo_owner(photo["user_id"], user_id, photo_id, "like")
                
                return {"success": True, "action": "liked", "liked": True}
                
        except Exception as e:
            logger.error(f"Like achievement photo error: {str(e)}")
            return {"success": False, "message": "Failed to process like"}

    async def _process_uploaded_image(self, file_path: str) -> str:
        """Process and optimize uploaded image"""
        try:
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large (max 2048x2048)
                img.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
                
                # Create processed filename
                base_name = os.path.basename(file_path)
                name, ext = os.path.splitext(base_name)
                processed_name = f"{name}_processed{ext}"
                processed_path = f"{self.custom_photos_dir}/{processed_name}"
                
                # Save optimized version
                img.save(processed_path, "JPEG", quality=85, optimize=True)
                
                return f"/uploads/custom_photos/{processed_name}"
                
        except Exception as e:
            logger.error(f"Process uploaded image error: {str(e)}")
            return f"/uploads/custom_photos/{os.path.basename(file_path)}"

    async def _generate_milestone_template(self, user_id: str, achievement_data: Dict[str, Any], style: str) -> str:
        """Generate milestone achievement template"""
        try:
            # Canvas size (Instagram Stories optimized)
            width, height = 1080, 1920
            
            if style == "modern":
                img = await self._create_modern_milestone_template(width, height, achievement_data)
            elif style == "celebration":
                img = await self._create_celebration_milestone_template(width, height, achievement_data)
            else:
                img = await self._create_classic_milestone_template(width, height, achievement_data)
            
            # Save image
            filename = f"milestone_{user_id}_{int(datetime.now(timezone.utc).timestamp())}.jpg"
            file_path = f"{self.achievement_dir}/{filename}"
            img.save(file_path, "JPEG", quality=90, optimize=True)
            
            return f"/uploads/achievements/{filename}"
            
        except Exception as e:
            logger.error(f"Generate milestone template error: {str(e)}")
            raise

    async def _create_modern_milestone_template(self, width: int, height: int, data: Dict[str, Any]) -> Image.Image:
        """Create modern style milestone template"""
        try:
            # Create gradient background
            img = Image.new('RGB', (width, height), self.brand_colors["background"])
            draw = ImageDraw.Draw(img)
            
            # Create gradient effect
            for y in range(height):
                ratio = y / height
                r1, g1, b1 = tuple(int(self.brand_colors["primary"][i:i+2], 16) for i in (1, 3, 5))
                r2, g2, b2 = tuple(int(self.brand_colors["accent"][i:i+2], 16) for i in (1, 3, 5))
                
                r = int(r1 * (1 - ratio) + r2 * ratio)
                g = int(g1 * (1 - ratio) + g2 * ratio)
                b = int(b1 * (1 - ratio) + b2 * ratio)
                
                draw.line([(0, y), (width, y)], fill=(r, g, b))
            
            # Add content overlay
            overlay = Image.new('RGBA', (width, height), (255, 255, 255, 240))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # Add rounded rectangle background for content
            content_margin = 120
            content_rect = [content_margin, height//4, width-content_margin, height*3//4]
            
            # Draw rounded rectangle (simplified)
            overlay_draw.rectangle(content_rect, fill=(255, 255, 255, 250))
            
            # Load fonts
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVu-Sans-Bold.ttf", 72)
                amount_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVu-Sans-Bold.ttf", 96)
                subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVu-Sans.ttf", 48)
                brand_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVu-Sans-Bold.ttf", 36)
            except:
                title_font = ImageFont.load_default()
                amount_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
                brand_font = ImageFont.load_default()
            
            # Add text content
            text_color = tuple(int(self.brand_colors["text_primary"][i:i+2], 16) for i in (1, 3, 5))
            accent_color = tuple(int(self.brand_colors["accent"][i:i+2], 16) for i in (1, 3, 5))
            
            # Title
            title = "🎉 Milestone Achieved!"
            title_bbox = overlay_draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            overlay_draw.text(((width - title_width) // 2, height//4 + 60), title, font=title_font, fill=text_color)
            
            # Amount (if provided)
            amount = data.get("amount")
            if amount:
                amount_text = f"₹{amount:,.0f}"
                amount_bbox = overlay_draw.textbbox((0, 0), amount_text, font=amount_font)
                amount_width = amount_bbox[2] - amount_bbox[0]
                overlay_draw.text(((width - amount_width) // 2, height//2 - 50), amount_text, font=amount_font, fill=accent_color)
            
            # Description
            description = data.get("description", "Great progress on your financial journey!")
            desc_lines = self._wrap_text(description, subtitle_font, width - 240)
            y_offset = height//2 + 80
            for line in desc_lines:
                line_bbox = overlay_draw.textbbox((0, 0), line, font=subtitle_font)
                line_width = line_bbox[2] - line_bbox[0]
                overlay_draw.text(((width - line_width) // 2, y_offset), line, font=subtitle_font, fill=text_color)
                y_offset += 60
            
            # Brand footer
            brand_text = "EarnNest - Your Financial Journey"
            brand_bbox = overlay_draw.textbbox((0, 0), brand_text, font=brand_font)
            brand_width = brand_bbox[2] - brand_bbox[0]
            overlay_draw.text(((width - brand_width) // 2, height - 150), brand_text, font=brand_font, fill=text_color)
            
            # Combine overlay with background
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
            
            return img
            
        except Exception as e:
            logger.error(f"Create modern milestone template error: {str(e)}")
            raise

    async def _create_celebration_milestone_template(self, width: int, height: int, data: Dict[str, Any]) -> Image.Image:
        """Create celebration style milestone template"""
        # Similar implementation with celebration theme
        # For brevity, using simplified version
        img = Image.new('RGB', (width, height), self.brand_colors["accent"])
        draw = ImageDraw.Draw(img)
        
        # Add celebration elements (stars, confetti effect)
        # This would include more elaborate graphics
        
        return img

    async def _create_classic_milestone_template(self, width: int, height: int, data: Dict[str, Any]) -> Image.Image:
        """Create classic style milestone template"""
        # Similar implementation with classic theme
        img = Image.new('RGB', (width, height), self.brand_colors["primary"])
        return img

    async def _generate_badge_template(self, user_id: str, achievement_data: Dict[str, Any], style: str) -> str:
        """Generate badge achievement template"""
        # Implementation for badge templates
        width, height = 1080, 1080
        img = Image.new('RGB', (width, height), self.brand_colors["purple"])
        
        filename = f"badge_{user_id}_{int(datetime.now(timezone.utc).timestamp())}.jpg"
        file_path = f"{self.achievement_dir}/{filename}"
        img.save(file_path, "JPEG", quality=90)
        
        return f"/uploads/achievements/{filename}"

    async def _generate_goal_template(self, user_id: str, achievement_data: Dict[str, Any], style: str) -> str:
        """Generate goal completion template"""
        width, height = 1080, 1080
        img = Image.new('RGB', (width, height), self.brand_colors["blue"])
        
        filename = f"goal_{user_id}_{int(datetime.now(timezone.utc).timestamp())}.jpg"
        file_path = f"{self.achievement_dir}/{filename}"
        img.save(file_path, "JPEG", quality=90)
        
        return f"/uploads/achievements/{filename}"

    async def _generate_streak_template(self, user_id: str, achievement_data: Dict[str, Any], style: str) -> str:
        """Generate streak achievement template"""
        width, height = 1080, 1080
        img = Image.new('RGB', (width, height), "#FF6B35")  # Orange for streaks
        
        filename = f"streak_{user_id}_{int(datetime.now(timezone.utc).timestamp())}.jpg"
        file_path = f"{self.achievement_dir}/{filename}"
        img.save(file_path, "JPEG", quality=90)
        
        return f"/uploads/achievements/{filename}"

    async def _generate_generic_template(self, user_id: str, achievement_data: Dict[str, Any], style: str) -> str:
        """Generate generic achievement template"""
        width, height = 1080, 1080
        img = Image.new('RGB', (width, height), self.brand_colors["primary"])
        
        filename = f"generic_{user_id}_{int(datetime.now(timezone.utc).timestamp())}.jpg"
        file_path = f"{self.achievement_dir}/{filename}"
        img.save(file_path, "JPEG", quality=90)
        
        return f"/uploads/achievements/{filename}"

    async def _create_achievement_overlay(self, achievement_data: Dict[str, Any]) -> Image.Image:
        """Create branded overlay for custom photos"""
        width, height = 1080, 1080
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Add semi-transparent branded elements
        # Badge in corner, text overlay, etc.
        
        return overlay

    async def _combine_photo_with_overlay(self, photo: Image.Image, overlay: Image.Image) -> Image.Image:
        """Combine user photo with branded overlay"""
        # Resize photo to fit canvas
        photo = photo.resize((1080, 1080), Image.Resampling.LANCZOS)
        
        # Combine with overlay
        combined = Image.alpha_composite(photo.convert('RGBA'), overlay)
        
        return combined.convert('RGB')

    def _is_valid_image_file(self, filename: str) -> bool:
        """Check if file is a valid image"""
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        return any(filename.lower().endswith(ext) for ext in allowed_extensions)

    def _wrap_text(self, text: str, font, max_width: int) -> List[str]:
        """Wrap text to fit within max width"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip()
            
            # Create a dummy draw to measure text
            dummy_img = Image.new('RGB', (1, 1))
            dummy_draw = ImageDraw.Draw(dummy_img)
            bbox = dummy_draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines

    async def _notify_photo_owner(self, owner_id: str, liker_id: str, photo_id: str, action: str):
        """Notify photo owner of interaction"""
        try:
            from push_notification_service import get_push_service
            
            # Get liker info
            from database import get_user_by_id
            liker = await get_user_by_id(liker_id)
            
            if liker:
                push_service = await get_push_service()
                if push_service:
                    notification_data = {
                        "reactor_name": liker.get("full_name", "Someone"),
                        "reactor_id": liker_id,
                        "photo_id": photo_id,
                        "action": action
                    }
                    
                    await push_service.send_photo_interaction_notification(owner_id, notification_data)
                    
        except Exception as e:
            logger.error(f"Notify photo owner error: {str(e)}")

# Global instance
enhanced_photo_service = None

async def get_enhanced_photo_service() -> EnhancedPhotoService:
    global enhanced_photo_service
    if enhanced_photo_service is None:
        db = await get_database()
        enhanced_photo_service = EnhancedPhotoService(db)
    return enhanced_photo_service
