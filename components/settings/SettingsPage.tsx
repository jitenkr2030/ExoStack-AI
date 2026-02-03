'use client'

import React, { useState, useEffect } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { 
  User, 
  Lock, 
  Bell, 
  Shield, 
  Laptop, 
  Save,
  Upload,
  CheckCircle,
  AlertCircle
} from 'lucide-react'

export default function SettingsPage() {
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })

  // Profile form state
  const [profile, setProfile] = useState({
    firstName: '',
    lastName: '',
    username: '',
    email: '',
    avatar: '',
    bio: '',
    company: '',
    location: '',
    website: '',
    github: '',
    twitter: '',
    linkedin: ''
  })

  // Password form state
  const [password, setPassword] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  })

  // Notification preferences
  const [notifications, setNotifications] = useState({
    emailDigest: true,
    taskNotifications: true,
    nodeAlerts: true
  })

  useEffect(() => {
    fetchUserProfile()
  }, [])

  const fetchUserProfile = async () => {
    try {
      const response = await fetch('/api/user/profile')
      if (response.ok) {
        const data = await response.json()
        setUser(data.user)
        
        // Set profile form data
        setProfile({
          firstName: data.user.firstName || '',
          lastName: data.user.lastName || '',
          username: data.user.username || '',
          email: data.user.email || '',
          avatar: data.user.avatar || '',
          bio: data.user.profile?.bio || '',
          company: data.user.profile?.company || '',
          location: data.user.profile?.location || '',
          website: data.user.profile?.website || '',
          github: data.user.profile?.github || '',
          twitter: data.user.profile?.twitter || '',
          linkedin: data.user.profile?.linkedin || ''
        })

        // Set notification preferences
        setNotifications({
          emailDigest: data.user.profile?.emailDigest ?? true,
          taskNotifications: data.user.profile?.taskNotifications ?? true,
          nodeAlerts: data.user.profile?.nodeAlerts ?? true
        })
      }
    } catch (error) {
      console.error('Failed to fetch user profile:', error)
    } finally {
      setLoading(false)
    }
  }

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text })
    setTimeout(() => setMessage({ type: '', text: }), 5000)
  }

  const handleProfileSave = async () => {
    setSaving(true)
    try {
      const response = await fetch('/api/user/profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...profile,
          ...notifications
        })
      })

      const data = await response.json()
      if (response.ok) {
        showMessage('success', 'Profile updated successfully!')
        setUser(data.user)
      } else {
        showMessage('error', data.error || 'Failed to update profile')
      }
    } catch (error) {
      showMessage('error', 'Network error. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  const handlePasswordSave = async () => {
    if (password.newPassword !== password.confirmPassword) {
      showMessage('error', 'Passwords do not match')
      return
    }

    setSaving(true)
    try {
      const response = await fetch('/api/user/password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          currentPassword: password.currentPassword,
          newPassword: password.newPassword
        })
      })

      const data = await response.json()
      if (response.ok) {
        showMessage('success', 'Password changed successfully!')
        setPassword({ currentPassword: '', newPassword: '', confirmPassword: '' })
      } else {
        showMessage('error', data.error || 'Failed to change password')
      }
    } catch (error) {
      showMessage('error', 'Network error. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  const handleAvatarUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      // In a real app, you'd upload to a service like Cloudinary or S3
      // For now, we'll use a placeholder URL
      const reader = new FileReader()
      reader.onloadend = () => {
        setProfile(prev => ({ ...prev, avatar: reader.result as string }))
      }
      reader.readAsDataURL(file)
    }
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600">Manage your account settings and preferences</p>
        </div>

        {message.text && (
          <Alert className={message.type === 'success' ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
            {message.type === 'success' ? (
              <CheckCircle className="h-4 w-4 text-green-600" />
            ) : (
              <AlertCircle className="h-4 w-4 text-red-600" />
            )}
            <AlertDescription className={message.type === 'success' ? 'text-green-800' : 'text-red-800'}>
              {message.text}
            </AlertDescription>
          </Alert>
        )}

        <Tabs defaultValue="profile" className="space-y-6">
          <TabsList>
            <TabsTrigger value="profile">Profile</TabsTrigger>
            <TabsTrigger value="security">Security</TabsTrigger>
            <TabsTrigger value="notifications">Notifications</TabsTrigger>
            <TabsTrigger value="account">Account</TabsTrigger>
          </TabsList>

          <TabsContent value="profile">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <User className="w-5 h-5 mr-2" />
                  Profile Information
                </CardTitle>
                <CardDescription>
                  Update your personal information and profile details
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Avatar Upload */}
                <div className="flex items-center space-x-4">
                  <Avatar className="w-20 h-20">
                    <AvatarImage src={profile.avatar} alt={profile.username} />
                    <AvatarFallback className="text-lg">
                      {profile.username?.charAt(0).toUpperCase() || 'U'}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <Label htmlFor="avatar-upload" className="cursor-pointer">
                      <Button variant="outline" size="sm" asChild>
                        <span>
                          <Upload className="w-4 h-4 mr-2" />
                          Change Avatar
                        </span>
                      </Button>
                    </Label>
                    <input
                      id="avatar-upload"
                      type="file"
                      accept="image/*"
                      onChange={handleAvatarUpload}
                      className="hidden"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      JPG, PNG or GIF. Max 2MB.
                    </p>
                  </div>
                </div>

                {/* Basic Information */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="firstName">First Name</Label>
                    <Input
                      id="firstName"
                      value={profile.firstName}
                      onChange={(e) => setProfile(prev => ({ ...prev, firstName: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName">Last Name</Label>
                    <Input
                      id="lastName"
                      value={profile.lastName}
                      onChange={(e) => setProfile(prev => ({ ...prev, lastName: e.target.value }))}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="username">Username</Label>
                    <Input
                      id="username"
                      value={profile.username}
                      onChange={(e) => setProfile(prev => ({ ...prev, username: e.target.value }))}
                      disabled
                    />
                    <p className="text-xs text-gray-500">Username cannot be changed</p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={profile.email}
                      onChange={(e) => setProfile(prev => ({ ...prev, email: e.target.value }))}
                      disabled
                    />
                    <p className="text-xs text-gray-500">Email cannot be changed</p>
                  </div>
                </div>

                {/* Additional Information */}
                <div className="space-y-2">
                  <Label htmlFor="bio">Bio</Label>
                  <Textarea
                    id="bio"
                    placeholder="Tell us about yourself"
                    value={profile.bio}
                    onChange={(e) => setProfile(prev => ({ ...prev, bio: e.target.value }))}
                    rows={3}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="company">Company</Label>
                    <Input
                      id="company"
                      value={profile.company}
                      onChange={(e) => setProfile(prev => ({ ...prev, company: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="location">Location</Label>
                    <Input
                      id="location"
                      value={profile.location}
                      onChange={(e) => setProfile(prev => ({ ...prev, location: e.target.value }))}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="website">Website</Label>
                  <Input
                    id="website"
                    type="url"
                    placeholder="https://yourwebsite.com"
                    value={profile.website}
                    onChange={(e) => setProfile(prev => ({ ...prev, website: e.target.value }))}
                  />
                </div>

                {/* Social Links */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="github">GitHub</Label>
                    <Input
                      id="github"
                      placeholder="username"
                      value={profile.github}
                      onChange={(e) => setProfile(prev => ({ ...prev, github: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="twitter">Twitter</Label>
                    <Input
                      id="twitter"
                      placeholder="@username"
                      value={profile.twitter}
                      onChange={(e) => setProfile(prev => ({ ...prev, twitter: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="linkedin">LinkedIn</Label>
                    <Input
                      id="linkedin"
                      placeholder="username"
                      value={profile.linkedin}
                      onChange={(e) => setProfile(prev => ({ ...prev, linkedin: e.target.value }))}
                    />
                  </div>
                </div>

                <Button onClick={handleProfileSave} disabled={saving}>
                  {saving ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="w-4 h-4 mr-2" />
                      Save Profile
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="security">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Lock className="w-5 h-5 mr-2" />
                  Change Password
                </CardTitle>
                <CardDescription>
                  Update your password to keep your account secure
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="currentPassword">Current Password</Label>
                  <Input
                    id="currentPassword"
                    type="password"
                    value={password.currentPassword}
                    onChange={(e) => setPassword(prev => ({ ...prev, currentPassword: e.target.value }))}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="newPassword">New Password</Label>
                  <Input
                    id="newPassword"
                    type="password"
                    value={password.newPassword}
                    onChange={(e) => setPassword(prev => ({ ...prev, newPassword: e.target.value }))}
                  />
                  <p className="text-xs text-gray-500">Minimum 6 characters</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">Confirm New Password</Label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    value={password.confirmPassword}
                    onChange={(e) => setPassword(prev => ({ ...prev, confirmPassword: e.target.value }))}
                  />
                </div>

                <Button onClick={handlePasswordSave} disabled={saving}>
                  {saving ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Updating...
                    </>
                  ) : (
                    <>
                      <Shield className="w-4 h-4 mr-2" />
                      Change Password
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="notifications">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Bell className="w-5 h-5 mr-2" />
                  Notification Preferences
                </CardTitle>
                <CardDescription>
                  Choose what notifications you want to receive
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Email Digest</Label>
                    <p className="text-sm text-gray-500">
                      Receive weekly summary of your AI compute activity
                    </p>
                  </div>
                  <Switch
                    checked={notifications.emailDigest}
                    onCheckedChange={(checked) => 
                      setNotifications(prev => ({ ...prev, emailDigest: checked }))
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Task Notifications</Label>
                    <p className="text-sm text-gray-500">
                      Get notified when your AI tasks complete or fail
                    </p>
                  </div>
                  <Switch
                    checked={notifications.taskNotifications}
                    onCheckedChange={(checked) => 
                      setNotifications(prev => ({ ...prev, taskNotifications: checked }))
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Node Alerts</Label>
                    <p className="text-sm text-gray-500">
                      Receive alerts when your nodes go offline or encounter issues
                    </p>
                  </div>
                  <Switch
                    checked={notifications.nodeAlerts}
                    onCheckedChange={(checked) => 
                      setNotifications(prev => ({ ...prev, nodeAlerts: checked }))
                    }
                  />
                </div>

                <Button onClick={handleProfileSave} disabled={saving}>
                  {saving ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="w-4 h-4 mr-2" />
                      Save Preferences
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="account">
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Laptop className="w-5 h-5 mr-2" />
                    Account Information
                  </CardTitle>
                  <CardDescription>
                    Your account details and usage limits
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label>Account Type</Label>
                      <div className="mt-1">
                        <Badge variant={user?.isPremium ? "default" : "secondary"}>
                          {user?.isPremium ? 'Premium' : 'Free'}
                        </Badge>
                      </div>
                    </div>
                    <div>
                      <Label>Member Since</Label>
                      <p className="text-sm text-gray-600 mt-1">
                        {user?.createdAt ? new Date(user.createdAt).toLocaleDateString() : 'Unknown'}
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label>Max Nodes</Label>
                      <p className="text-2xl font-bold text-blue-600">{user?.maxNodes || 5}</p>
                    </div>
                    <div>
                      <Label>Max Tasks</Label>
                      <p className="text-2xl font-bold text-green-600">{user?.maxTasks || 100}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label>Total Logins</Label>
                      <p className="text-lg font-semibold">{user?.loginCount || 0}</p>
                    </div>
                    <div>
                      <Label>Last Login</Label>
                      <p className="text-sm text-gray-600">
                        {user?.lastLogin ? new Date(user.lastLogin).toLocaleString() : 'Never'}
                      </p>
                    </div>
                  </div>

                  {!user?.isPremium && (
                    <div className="pt-4 border-t">
                      <Button className="w-full">
                        Upgrade to Premium
                      </Button>
                      <p className="text-xs text-gray-500 mt-2 text-center">
                        Unlock unlimited nodes and advanced features
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  )
}