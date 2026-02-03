'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Laptop, Zap, Battery, Wifi, Shield, Github, Twitter } from 'lucide-react'

interface AuthFormProps {
  onSuccess?: () => void
}

export default function AuthForm({ onSuccess }: AuthFormProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const router = useRouter()

  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')
    setSuccess('')

    const formData = new FormData(e.currentTarget)
    const email = formData.get('email') as string
    const password = formData.get('password') as string

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })

      const data = await response.json()

      if (response.ok) {
        setSuccess('Login successful! Redirecting...')
        setTimeout(() => {
          router.push('/dashboard')
          onSuccess?.()
        }, 1000)
      } else {
        setError(data.error || 'Login failed')
      }
    } catch (err) {
      setError('Network error. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleRegister = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')
    setSuccess('')

    const formData = new FormData(e.currentTarget)
    const email = formData.get('email') as string
    const username = formData.get('username') as string
    const password = formData.get('password') as string
    const firstName = formData.get('firstName') as string
    const lastName = formData.get('lastName') as string

    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          email, 
          username, 
          password, 
          firstName, 
          lastName 
        }),
      })

      const data = await response.json()

      if (response.ok) {
        setSuccess('Registration successful! Redirecting...')
        setTimeout(() => {
          router.push('/dashboard')
          onSuccess?.()
        }, 1000)
      } else {
        setError(data.error || 'Registration failed')
      }
    } catch (err) {
      setError('Network error. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-6xl grid lg:grid-cols-2 gap-8 items-center">
        {/* Left Side - Hero Content */}
        <div className="text-center lg:text-left space-y-6">
          <div className="flex items-center justify-center lg:justify-start space-x-3">
            <Laptop className="w-10 h-10 text-blue-600" />
            <h1 className="text-4xl font-bold text-gray-900">ExoStack AI</h1>
          </div>
          
          <h2 className="text-2xl font-semibold text-gray-800">
            Turn Your Idle Laptop into an AI Powerhouse
          </h2>
          
          <p className="text-lg text-gray-600 leading-relaxed">
            Join thousands of users who are transforming their unused laptop time into 
            valuable AI computation. Earn rewards while contributing to the future of 
            distributed artificial intelligence.
          </p>

          <div className="grid grid-cols-2 gap-4 pt-4">
            <div className="flex items-center space-x-3">
              <Zap className="w-5 h-5 text-yellow-500" />
              <span className="text-sm font-medium text-gray-700">AI-Ready Detection</span>
            </div>
            <div className="flex items-center space-x-3">
              <Battery className="w-5 h-5 text-green-500" />
              <span className="text-sm font-medium text-gray-700">Smart Power Management</span>
            </div>
            <div className="flex items-center space-x-3">
              <Wifi className="w-5 h-5 text-blue-500" />
              <span className="text-sm font-medium text-gray-700">Distributed Computing</span>
            </div>
            <div className="flex items-center space-x-3">
              <Shield className="w-5 h-5 text-purple-500" />
              <span className="text-sm font-medium text-gray-700">Privacy-First</span>
            </div>
          </div>

          <div className="flex justify-center lg:justify-start space-x-4 pt-4">
            <Button variant="outline" size="sm" className="flex items-center space-x-2">
              <Github className="w-4 h-4" />
              <span>GitHub</span>
            </Button>
            <Button variant="outline" size="sm" className="flex items-center space-x-2">
              <Twitter className="w-4 h-4" />
              <span>Twitter</span>
            </Button>
          </div>
        </div>

        {/* Right Side - Auth Forms */}
        <div className="w-full max-w-md mx-auto">
          <Tabs defaultValue="login" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="login">Sign In</TabsTrigger>
              <TabsTrigger value="register">Sign Up</TabsTrigger>
            </TabsList>
            
            <TabsContent value="login">
              <Card>
                <CardHeader>
                  <CardTitle>Welcome Back</CardTitle>
                  <CardDescription>
                    Sign in to access your AI compute dashboard
                  </CardDescription>
                </CardHeader>
                <form onSubmit={handleLogin}>
                  <CardContent className="space-y-4">
                    {error && (
                      <Alert variant="destructive">
                        <AlertDescription>{error}</AlertDescription>
                      </Alert>
                    )}
                    {success && (
                      <Alert>
                        <AlertDescription className="text-green-600">{success}</AlertDescription>
                      </Alert>
                    )}
                    
                    <div className="space-y-2">
                      <Label htmlFor="login-email">Email</Label>
                      <Input
                        id="login-email"
                        name="email"
                        type="email"
                        placeholder="Enter your email"
                        required
                        disabled={isLoading}
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="login-password">Password</Label>
                      <Input
                        id="login-password"
                        name="password"
                        type="password"
                        placeholder="Enter your password"
                        required
                        disabled={isLoading}
                      />
                    </div>
                  </CardContent>
                  
                  <CardFooter className="flex flex-col space-y-4">
                    <Button 
                      type="submit" 
                      className="w-full" 
                      disabled={isLoading}
                    >
                      {isLoading ? 'Signing in...' : 'Sign In'}
                    </Button>
                    
                    <div className="text-center text-sm text-gray-600">
                      <a href="#" className="text-blue-600 hover:underline">
                        Forgot your password?
                      </a>
                    </div>
                  </CardFooter>
                </form>
              </Card>
            </TabsContent>
            
            <TabsContent value="register">
              <Card>
                <CardHeader>
                  <CardTitle>Create Account</CardTitle>
                  <CardDescription>
                    Join the ExoStack AI community and start earning
                  </CardDescription>
                </CardHeader>
                <form onSubmit={handleRegister}>
                  <CardContent className="space-y-4">
                    {error && (
                      <Alert variant="destructive">
                        <AlertDescription>{error}</AlertDescription>
                      </Alert>
                    )}
                    {success && (
                      <Alert>
                        <AlertDescription className="text-green-600">{success}</AlertDescription>
                      </Alert>
                    )}
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="register-firstName">First Name</Label>
                        <Input
                          id="register-firstName"
                          name="firstName"
                          type="text"
                          placeholder="First name"
                          disabled={isLoading}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="register-lastName">Last Name</Label>
                        <Input
                          id="register-lastName"
                          name="lastName"
                          type="text"
                          placeholder="Last name"
                          disabled={isLoading}
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="register-username">Username</Label>
                      <Input
                        id="register-username"
                        name="username"
                        type="text"
                        placeholder="Choose a username"
                        required
                        disabled={isLoading}
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="register-email">Email</Label>
                      <Input
                        id="register-email"
                        name="email"
                        type="email"
                        placeholder="Enter your email"
                        required
                        disabled={isLoading}
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="register-password">Password</Label>
                      <Input
                        id="register-password"
                        name="password"
                        type="password"
                        placeholder="Create a password (min 6 chars)"
                        required
                        minLength={6}
                        disabled={isLoading}
                      />
                    </div>
                  </CardContent>
                  
                  <CardFooter className="flex flex-col space-y-4">
                    <Button 
                      type="submit" 
                      className="w-full" 
                      disabled={isLoading}
                    >
                      {isLoading ? 'Creating account...' : 'Create Account'}
                    </Button>
                    
                    <div className="text-center text-xs text-gray-600">
                      By creating an account, you agree to our{' '}
                      <a href="#" className="text-blue-600 hover:underline">Terms</a> and{' '}
                      <a href="#" className="text-blue-600 hover:underline">Privacy Policy</a>
                    </div>
                  </CardFooter>
                </form>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  )
}