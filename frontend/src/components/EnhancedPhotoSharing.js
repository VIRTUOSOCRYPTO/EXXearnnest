import React, { useState, useEffect, useRef } from 'react';
import { Card, CardHeader, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';

const EnhancedPhotoSharing = ({ userId, achievementId, achievementData }) => {
  const [photos, setPhotos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [activeTab, setActiveTab] = useState('gallery');
  const [selectedTemplate, setSelectedTemplate] = useState('modern');
  const [showUpload, setShowUpload] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchUserPhotos();
  }, [userId]);

  const fetchUserPhotos = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/photos/achievements?limit=20`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setPhotos(data.photos);
      } else {
        console.error('Failed to fetch photos');
      }
    } catch (error) {
      console.error('Error fetching photos:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert('File size must be less than 5MB');
      return;
    }

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }

    try {
      setUploading(true);
      const token = localStorage.getItem('token');
      
      const formData = new FormData();
      formData.append('file', file);
      if (achievementId) {
        formData.append('achievement_id', achievementId);
      }

      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/photos/achievements/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      const result = await response.json();
      
      if (result.success) {
        alert('Photo uploaded successfully!');
        fetchUserPhotos(); // Refresh the gallery
        setShowUpload(false);
      } else {
        alert(result.message || 'Failed to upload photo');
      }
    } catch (error) {
      console.error('Error uploading photo:', error);
      alert('Failed to upload photo. Please try again.');
    } finally {
      setUploading(false);
      event.target.value = ''; // Reset file input
    }
  };

  const generateBrandedPhoto = async () => {
    if (!achievementData) {
      alert('No achievement data available for photo generation');
      return;
    }

    try {
      setGenerating(true);
      const token = localStorage.getItem('token');
      
      const photoData = {
        ...achievementData,
        template_style: selectedTemplate,
        achievement_id: achievementId || achievementData.achievement_id
      };

      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/photos/achievements/generate-branded`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(photoData),
      });

      const result = await response.json();
      
      if (result.success) {
        alert('Branded photo generated successfully!');
        fetchUserPhotos(); // Refresh the gallery
      } else {
        alert(result.message || 'Failed to generate photo');
      }
    } catch (error) {
      console.error('Error generating photo:', error);
      alert('Failed to generate photo. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  const likePhoto = async (photoId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/photos/${photoId}/like`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      const result = await response.json();
      
      if (result.success) {
        // Update local state
        setPhotos(prevPhotos => 
          prevPhotos.map(photo => 
            photo.id === photoId 
              ? { 
                  ...photo, 
                  user_liked: result.liked,
                  like_count: result.liked ? photo.like_count + 1 : photo.like_count - 1
                }
              : photo
          )
        );
      }
    } catch (error) {
      console.error('Error liking photo:', error);
    }
  };

  const sharePhoto = (photo) => {
    if (navigator.share) {
      navigator.share({
        title: 'My Achievement Photo - EarnAura',
        text: `Check out my achievement on EarnAura!`,
        url: `${window.location.origin}${photo.final_photo_url}`,
      });
    } else {
      // Fallback to copying URL
      const shareUrl = `${window.location.origin}${photo.final_photo_url}`;
      navigator.clipboard.writeText(shareUrl).then(() => {
        alert('Photo link copied to clipboard!');
      });
    }
  };

  const downloadPhoto = (photo) => {
    const link = document.createElement('a');
    link.href = photo.final_photo_url;
    link.download = `achievement-${photo.id}.jpg`;
    link.click();
  };

  const getPhotoTypeIcon = (photoType) => {
    const icons = {
      custom: '📸',
      branded_template: '🎨',
      combined: '✨'
    };
    return icons[photoType] || '📷';
  };

  const getPhotoTypeBadge = (photoType) => {
    const labels = {
      custom: 'Custom Photo',
      branded_template: 'Branded Template',
      combined: 'Combined'
    };
    return labels[photoType] || photoType;
  };

  const templates = [
    { id: 'modern', name: 'Modern', preview: '🎨', description: 'Clean and professional design' },
    { id: 'celebration', name: 'Celebration', preview: '🎉', description: 'Festive with confetti and animations' },
    { id: 'classic', name: 'Classic', preview: '🏛️', description: 'Traditional and elegant style' },
    { id: 'minimal', name: 'Minimal', preview: '⚪', description: 'Simple and focused design' }
  ];

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map(i => (
          <Card key={i} className="w-full">
            <CardContent className="p-4">
              <div className="animate-pulse">
                <div className="h-32 bg-gray-200 rounded mb-4"></div>
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Card className="w-full">
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900">📸 Achievement Photos</h2>
            <div className="flex space-x-2">
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => setShowUpload(!showUpload)}
              >
                📤 Upload Photo
              </Button>
              {achievementData && (
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setActiveTab('create')}
                >
                  🎨 Create Branded
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="gallery">🖼️ Gallery</TabsTrigger>
          <TabsTrigger value="create">✨ Create</TabsTrigger>
        </TabsList>

        {/* Photo Gallery */}
        <TabsContent value="gallery" className="space-y-4 mt-6">
          {/* Upload Section */}
          {showUpload && (
            <Card className="w-full border-dashed border-2 border-blue-300">
              <CardContent className="p-6">
                <div className="text-center">
                  <div className="text-4xl mb-4">📤</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Upload Your Achievement Photo</h3>
                  <p className="text-gray-600 mb-4">Share a custom photo of your achievement</p>
                  
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  
                  <Button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploading}
                    className="mb-2"
                  >
                    {uploading ? 'Uploading...' : 'Choose Photo'}
                  </Button>
                  
                  <p className="text-xs text-gray-500">
                    Max size: 5MB • Formats: JPG, PNG, GIF, WebP
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Photos Grid */}
          {photos.length === 0 ? (
            <Card className="w-full">
              <CardContent className="p-8 text-center">
                <div className="text-6xl mb-4">📸</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Photos Yet</h3>
                <p className="text-gray-600 mb-4">Upload custom photos or create branded achievement images!</p>
                <div className="flex justify-center space-x-2">
                  <Button onClick={() => setShowUpload(true)}>
                    📤 Upload Photo
                  </Button>
                  {achievementData && (
                    <Button variant="outline" onClick={() => setActiveTab('create')}>
                      🎨 Create Branded
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {photos.map((photo) => (
                <Card key={photo.id} className="w-full hover:shadow-lg transition-shadow duration-200">
                  <CardContent className="p-4">
                    {/* Photo Image */}
                    <div className="relative mb-3">
                      <img
                        src={photo.final_photo_url}
                        alt="Achievement"
                        className="w-full h-48 object-cover rounded-lg"
                      />
                      <div className="absolute top-2 left-2">
                        <Badge variant="secondary" className="text-xs">
                          {getPhotoTypeIcon(photo.photo_type)} {getPhotoTypeBadge(photo.photo_type)}
                        </Badge>
                      </div>
                    </div>

                    {/* Photo Metadata */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">
                          {new Date(photo.created_at).toLocaleDateString()}
                        </span>
                        <div className="flex items-center space-x-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => likePhoto(photo.id)}
                            className={`flex items-center space-x-1 ${
                              photo.user_liked ? 'text-red-500' : 'text-gray-500'
                            }`}
                          >
                            <span>{photo.user_liked ? '❤️' : '🤍'}</span>
                            <span className="text-xs">{photo.like_count}</span>
                          </Button>
                        </div>
                      </div>

                      {/* Achievement Info */}
                      {photo.achievement_type && (
                        <div className="text-xs text-gray-500">
                          <Badge variant="outline" className="text-xs">
                            {photo.achievement_type.replace('_', ' ')}
                          </Badge>
                        </div>
                      )}

                      {/* Action Buttons */}
                      <div className="flex space-x-1">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => sharePhoto(photo)}
                          className="flex-1 text-xs"
                        >
                          📤 Share
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => downloadPhoto(photo)}
                          className="flex-1 text-xs"
                        >
                          💾 Download
                        </Button>
                      </div>

                      {/* Tags */}
                      {photo.tags && photo.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {photo.tags.slice(0, 3).map((tag, index) => (
                            <Badge key={index} variant="outline" className="text-xs">
                              #{tag}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Create Branded Photo */}
        <TabsContent value="create" className="space-y-4 mt-6">
          {!achievementData ? (
            <Card className="w-full">
              <CardContent className="p-8 text-center">
                <div className="text-6xl mb-4">🎨</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Achievement Data</h3>
                <p className="text-gray-600">Achievement information is needed to create branded photos.</p>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* Template Selection */}
              <Card className="w-full">
                <CardHeader>
                  <h3 className="text-lg font-medium text-gray-900">Choose a Template</h3>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {templates.map((template) => (
                      <div
                        key={template.id}
                        onClick={() => setSelectedTemplate(template.id)}
                        className={`p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                          selectedTemplate === template.id
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <div className="text-center">
                          <div className="text-3xl mb-2">{template.preview}</div>
                          <h4 className="font-medium text-sm text-gray-900">{template.name}</h4>
                          <p className="text-xs text-gray-600 mt-1">{template.description}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Achievement Preview */}
              <Card className="w-full">
                <CardHeader>
                  <h3 className="text-lg font-medium text-gray-900">Achievement Preview</h3>
                </CardHeader>
                <CardContent>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center space-x-3 mb-3">
                      <span className="text-3xl">{achievementData.icon || '🏆'}</span>
                      <div>
                        <h4 className="font-medium text-gray-900">
                          {achievementData.title || 'Achievement Unlocked'}
                        </h4>
                        <p className="text-sm text-gray-600">
                          {achievementData.description || 'Congratulations on your progress!'}
                        </p>
                      </div>
                    </div>
                    {achievementData.amount && (
                      <div className="text-lg font-bold text-green-600">
                        ₹{achievementData.amount.toLocaleString()}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Generate Button */}
              <Card className="w-full">
                <CardContent className="p-6 text-center">
                  <Button
                    onClick={generateBrandedPhoto}
                    disabled={generating}
                    size="lg"
                    className="w-full max-w-md"
                  >
                    {generating ? (
                      <div className="flex items-center space-x-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        <span>Generating...</span>
                      </div>
                    ) : (
                      <>✨ Generate Branded Photo</>
                    )}
                  </Button>
                  <p className="text-sm text-gray-600 mt-2">
                    Create a professional branded image using the {templates.find(t => t.id === selectedTemplate)?.name} template
                  </p>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default EnhancedPhotoSharing;
