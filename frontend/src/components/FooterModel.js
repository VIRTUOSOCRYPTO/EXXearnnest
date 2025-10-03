import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

const FooterModal = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-gradient-to-r from-emerald-50 to-blue-50 px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-[#00CC7E] rounded-lg flex items-center justify-center mr-3">
              <span className="text-white text-lg font-bold">₹</span>
            </div>
            <div>
              <h2 className="text-xl font-bold text-[#00CC7E]">
                {title}
              </h2>
              <p className="text-sm text-gray-600">EarnAura - Your Financial Companion</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <XMarkIcon className="w-6 h-6 text-gray-500" />
          </button>
        </div>
        
        {/* Content */}
        <div className="p-6">
          {children}
        </div>
      </div>
    </div>
  );
};

const AboutUsContent = () => (
  <div className="space-y-6">
    <div className="text-center mb-8">
      <div className="flex items-center justify-center mb-4">
        <div className="w-16 h-16 bg-[#00CC7E] rounded-lg flex items-center justify-center mr-4">
          <span className="text-white text-3xl font-bold">₹</span>
        </div>
        <h1 className="text-3xl font-bold text-[#00CC7E]">
          EarnAura
        </h1>
      </div>
      <p className="text-xl text-gray-600">Your Trusted Companion for Financial Success</p>
    </div>

    <div className="grid md:grid-cols-2 gap-8">
      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-4">Our Mission</h3>
        <p className="text-gray-600 leading-relaxed">
          EarnAura is dedicated to empowering students and professionals to take control of their financial future. 
          We believe that financial literacy and smart money management should be accessible to everyone, regardless 
          of their background or experience level.
        </p>
      </div>
      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-4">Our Vision</h3>
        <p className="text-gray-600 leading-relaxed">
          To create a world where every individual has the tools, knowledge, and confidence to build wealth, 
          achieve their financial goals, and secure their future through smart budgeting, goal setting, and 
          income diversification.
        </p>
      </div>
    </div>

    <div className="bg-gradient-to-r from-emerald-50 to-blue-50 p-6 rounded-lg">
      <h3 className="text-xl font-semibold text-gray-800 mb-4">What We Offer</h3>
      <div className="grid md:grid-cols-3 gap-4">
        <div className="text-center">
          <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center mx-auto mb-2">
            <span className="text-2xl">💰</span>
          </div>
          <h4 className="font-semibold text-gray-800">Smart Budgeting</h4>
          <p className="text-sm text-gray-600">AI-powered budget allocation and expense tracking</p>
        </div>
        <div className="text-center">
          <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-2">
            <span className="text-2xl">🎯</span>
          </div>
          <h4 className="font-semibold text-gray-800">Financial Goals</h4>
          <p className="text-sm text-gray-600">Set, track, and achieve your financial milestones</p>
        </div>
        <div className="text-center">
          <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-2">
            <span className="text-2xl">💼</span>
          </div>
          <h4 className="font-semibold text-gray-800">Side Hustles</h4>
          <p className="text-sm text-gray-600">Discover opportunities to increase your income</p>
        </div>
      </div>
    </div>

    <div>
      <h3 className="text-xl font-semibold text-gray-800 mb-4">Our Story</h3>
      <p className="text-gray-600 leading-relaxed">
        Founded with the belief that financial empowerment should be accessible to everyone, EarnAura was created 
        to bridge the gap between financial education and practical money management. We understand the unique 
        challenges faced by students and young professionals in today's economy, and we've built a platform that 
        grows with you on your financial journey.
      </p>
    </div>

    <div className="text-center bg-gray-50 p-6 rounded-lg">
      <h3 className="text-lg font-semibold text-gray-800 mb-2">Ready to Start Your Financial Journey?</h3>
      <p className="text-gray-600 mb-4">Join thousands of users who are already building their financial future with EarnAura.</p>
      <a href="mailto:tortoor8@gmail.com" className="inline-flex items-center px-6 py-3 bg-[#00CC7E] text-white rounded-lg hover:bg-[#00BB70] transition-colors font-medium">
        Get in Touch
      </a>
    </div>
  </div>
);

const PrivacyContent = () => (
  <div className="space-y-6">
    <div className="text-center mb-6">
      <h1 className="text-2xl font-bold text-gray-800 mb-2">Privacy Policy</h1>
      <p className="text-gray-600">Last updated: January 2025</p>
    </div>

    <div className="space-y-6">
      <section>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Information We Collect</h3>
        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="font-semibold text-gray-700 mb-2">Personal Information:</h4>
          <ul className="list-disc list-inside text-gray-600 space-y-1">
            <li>Name, email address, and contact information</li>
            <li>Profile information including skills and preferences</li>
            <li>Financial data you choose to input (budgets, goals, transactions)</li>
            <li>Usage data and analytics to improve our services</li>
          </ul>
        </div>
      </section>

      <section>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">How We Use Your Information</h3>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="bg-emerald-50 p-4 rounded-lg">
            <h4 className="font-semibold text-emerald-800 mb-2">Service Provision:</h4>
            <ul className="list-disc list-inside text-emerald-700 text-sm space-y-1">
              <li>Provide personalized financial insights</li>
              <li>Track your budgets and financial goals</li>
              <li>Suggest relevant side hustles and opportunities</li>
              <li>Generate AI-powered recommendations</li>
            </ul>
          </div>
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-semibold text-blue-800 mb-2">Communication:</h4>
            <ul className="list-disc list-inside text-blue-700 text-sm space-y-1">
              <li>Send important account updates</li>
              <li>Provide customer support</li>
              <li>Share relevant financial tips and content</li>
              <li>Respond to your inquiries</li>
            </ul>
          </div>
        </div>
      </section>

      <section>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Data Security</h3>
        <div className="bg-gradient-to-r from-green-50 to-blue-50 p-6 rounded-lg">
          <div className="grid md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                <span className="text-2xl">🔒</span>
              </div>
              <h4 className="font-semibold">Bank-Level Security</h4>
              <p className="text-sm text-gray-600">256-bit SSL encryption for all data</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                <span className="text-2xl">🛡️</span>
              </div>
              <h4 className="font-semibold">Secure Storage</h4>
              <p className="text-sm text-gray-600">Data stored on secure, monitored servers</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                <span className="text-2xl">🔐</span>
              </div>
              <h4 className="font-semibold">Access Control</h4>
              <p className="text-sm text-gray-600">Strict access controls and authentication</p>
            </div>
          </div>
        </div>
      </section>

      <section>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Your Rights</h3>
        <div className="space-y-3">
          <div className="flex items-start space-x-3">
            <span className="text-[#00CC7E] font-bold">•</span>
            <div>
              <h4 className="font-semibold text-gray-800">Access & Portability</h4>
              <p className="text-gray-600 text-sm">Request a copy of your personal data at any time</p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <span className="text-[#00CC7E] font-bold">•</span>
            <div>
              <h4 className="font-semibold text-gray-800">Correction & Update</h4>
              <p className="text-gray-600 text-sm">Update or correct your information through your profile</p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <span className="text-[#00CC7E] font-bold">•</span>
            <div>
              <h4 className="font-semibold text-gray-800">Deletion</h4>
              <p className="text-gray-600 text-sm">Request deletion of your account and associated data</p>
            </div>
          </div>
        </div>
      </section>
    </div>

    <div className="border-t pt-6 text-center">
      <p className="text-gray-600 mb-4">Questions about our privacy practices?</p>
      <a href="mailto:tortoor8@gmail.com?subject=Privacy%20Policy%20Question" className="text-[#00CC7E] hover:text-[#00BB70] font-medium">
        Contact us at tortoor8@gmail.com
      </a>
    </div>
  </div>
);

const SupportContent = () => (
  <div className="space-y-6">
    <div className="text-center mb-6">
      <h1 className="text-2xl font-bold text-gray-800 mb-2">Support Center</h1>
      <p className="text-gray-600">We're here to help you succeed with EarnAura</p>
    </div>

    <div className="grid md:grid-cols-2 gap-6">
      <div className="bg-gradient-to-br from-emerald-50 to-emerald-100 p-6 rounded-lg">
        <h3 className="text-xl font-semibold text-emerald-800 mb-4">Contact Support</h3>
        <div className="space-y-3">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">📧</span>
            <div>
              <h4 className="font-semibold text-[#00CC7E]">Email Support</h4>
              <a href="mailto:tortoor8@gmail.com" className="text-[#00CC7E] hover:text-[#00BB70]">
                tortoor8@gmail.com
              </a>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <span className="text-2xl">⏰</span>
            <div>
              <h4 className="font-semibold text-[#00CC7E]">Response Time</h4>
              <p className="text-[#00CC7E]">Within 24 hours</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <span className="text-2xl">🌍</span>
            <div>
              <h4 className="font-semibold text-[#00CC7E]">Availability</h4>
              <p className="text-[#00CC7E]">24/7 Email Support</p>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-lg">
        <h3 className="text-xl font-semibold text-blue-800 mb-4">Quick Help</h3>
        <div className="space-y-2">
          <a href="#faq" className="block p-3 bg-white rounded-lg hover:bg-blue-50 transition-colors">
            <div className="flex items-center justify-between">
              <span className="font-medium text-blue-800">Frequently Asked Questions</span>
              <span className="text-blue-600">→</span>
            </div>
          </a>
          <a href="#guides" className="block p-3 bg-white rounded-lg hover:bg-blue-50 transition-colors">
            <div className="flex items-center justify-between">
              <span className="font-medium text-blue-800">User Guides & Tutorials</span>
              <span className="text-blue-600">→</span>
            </div>
          </a>
          <a href="#video" className="block p-3 bg-white rounded-lg hover:bg-blue-50 transition-colors">
            <div className="flex items-center justify-between">
              <span className="font-medium text-blue-800">Video Tutorials</span>
              <span className="text-blue-600">→</span>
            </div>
          </a>
        </div>
      </div>
    </div>

    <div>
      <h3 className="text-xl font-semibold text-gray-800 mb-4">Frequently Asked Questions</h3>
      <div className="space-y-4">
        <div className="border border-gray-200 rounded-lg p-4">
          <h4 className="font-semibold text-gray-800 mb-2">How do I set up my first budget?</h4>
          <p className="text-gray-600">Navigate to the Budget section, enter your monthly income, and allocate amounts to different categories like Food, Transportation, Entertainment, etc. EarnAura will help you track spending against these allocations.</p>
        </div>
        <div className="border border-gray-200 rounded-lg p-4">
          <h4 className="font-semibold text-gray-800 mb-2">Are my financial data secure?</h4>
          <p className="text-gray-600">Absolutely! We use bank-level 256-bit SSL encryption to protect your data. Your financial information is never shared with third parties and is stored on secure, monitored servers.</p>
        </div>
        <div className="border border-gray-200 rounded-lg p-4">
          <h4 className="font-semibold text-gray-800 mb-2">How do I find relevant side hustles?</h4>
          <p className="text-gray-600">Based on the skills you select during registration, EarnAura provides personalized side hustle recommendations. You can also browse opportunities posted by other users and apply directly through the platform.</p>
        </div>
        <div className="border border-gray-200 rounded-lg p-4">
          <h4 className="font-semibold text-gray-800 mb-2">Can I export my financial data?</h4>
          <p className="text-gray-600">Yes! You can request a complete export of your financial data at any time by contacting our support team. We believe in data portability and transparency.</p>
        </div>
      </div>
    </div>

    <div className="bg-gradient-to-r from-emerald-50 to-blue-50 p-6 rounded-lg text-center">
      <h3 className="text-lg font-semibold text-gray-800 mb-2">Still Need Help?</h3>
      <p className="text-gray-600 mb-4">Our support team is always ready to assist you with any questions or concerns.</p>
      <a 
        href="mailto:tortoor8@gmail.com?subject=EarnAura%20Support%20Request"
        className="inline-flex items-center px-6 py-3 bg-[#00CC7E] text-white rounded-lg hover:bg-[#00BB70] transition-colors font-medium"
      >
        Contact Support Team
      </a>
    </div>
  </div>
);

const TermsContent = () => (
  <div className="space-y-6">
    <div className="text-center mb-6">
      <h1 className="text-2xl font-bold text-gray-800 mb-2">Terms of Service</h1>
      <p className="text-gray-600">Last updated: January 2025</p>
    </div>

    <div className="space-y-6">
      <section>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Acceptance of Terms</h3>
        <p className="text-gray-600 leading-relaxed">
          By accessing and using EarnAura ("the Service"), you accept and agree to be bound by the terms 
          and provision of this agreement. If you do not agree to abide by the above, please do not use this service.
        </p>
      </section>

      <section>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Service Description</h3>
        <div className="bg-gradient-to-r from-emerald-50 to-blue-50 p-4 rounded-lg">
          <p className="text-gray-700 mb-3">EarnAura provides:</p>
          <div className="grid md:grid-cols-2 gap-4">
            <ul className="list-disc list-inside text-gray-600 space-y-1">
              <li>Personal budget tracking and management tools</li>
              <li>Financial goal setting and progress monitoring</li>
              <li>Side hustle discovery and application platform</li>
              <li>AI-powered financial insights and recommendations</li>
            </ul>
            <ul className="list-disc list-inside text-gray-600 space-y-1">
              <li>Expense categorization and analysis</li>
              <li>Income tracking and optimization suggestions</li>
              <li>Educational financial content and resources</li>
              <li>Community-driven opportunities marketplace</li>
            </ul>
          </div>
        </div>
      </section>

      <section>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">User Responsibilities</h3>
        <div className="space-y-3">
          <div className="border-l-4 border-emerald-500 pl-4">
            <h4 className="font-semibold text-gray-800">Account Security</h4>
            <p className="text-gray-600 text-sm">You are responsible for maintaining the confidentiality of your account credentials and for all activities under your account.</p>
          </div>
          <div className="border-l-4 border-blue-500 pl-4">
            <h4 className="font-semibold text-gray-800">Accurate Information</h4>
            <p className="text-gray-600 text-sm">You agree to provide accurate, current, and complete information during registration and to update such information as needed.</p>
          </div>
          <div className="border-l-4 border-purple-500 pl-4">
            <h4 className="font-semibold text-gray-800">Appropriate Use</h4>
            <p className="text-gray-600 text-sm">You agree to use the service only for lawful purposes and in accordance with these Terms of Service.</p>
          </div>
        </div>
      </section>

      <section>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Financial Disclaimer</h3>
        <div className="bg-amber-50 border border-amber-200 p-4 rounded-lg">
          <div className="flex items-start space-x-3">
            <span className="text-amber-600 text-xl">⚠️</span>
            <div>
              <h4 className="font-semibold text-amber-800 mb-2">Important Notice</h4>
              <p className="text-amber-700 text-sm leading-relaxed">
                EarnAura provides tools and information for educational and organizational purposes only. 
                We do not provide financial advice, investment recommendations, or guarantee any financial outcomes. 
                Always consult with qualified financial professionals for personalized advice.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Prohibited Activities</h3>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="bg-red-50 p-4 rounded-lg">
            <h4 className="font-semibold text-red-800 mb-2">Account Misuse:</h4>
            <ul className="list-disc list-inside text-red-700 text-sm space-y-1">
              <li>Creating fake or multiple accounts</li>
              <li>Sharing account credentials</li>
              <li>Impersonating other users</li>
              <li>Automated account creation</li>
            </ul>
          </div>
          <div className="bg-orange-50 p-4 rounded-lg">
            <h4 className="font-semibold text-orange-800 mb-2">Platform Abuse:</h4>
            <ul className="list-disc list-inside text-orange-700 text-sm space-y-1">
              <li>Posting fraudulent opportunities</li>
              <li>Spam or excessive messaging</li>
              <li>Attempting to hack or disrupt service</li>
              <li>Violating intellectual property rights</li>
            </ul>
          </div>
        </div>
      </section>

      <section>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Service Availability</h3>
        <p className="text-gray-600 leading-relaxed">
          While we strive to provide continuous service availability, EarnAura reserves the right to modify, 
          suspend, or discontinue any part of the service with or without notice. We are not liable for any 
          modification, suspension, or discontinuation of the service.
        </p>
      </section>

      <section>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Changes to Terms</h3>
        <div className="bg-gray-50 p-4 rounded-lg">
          <p className="text-gray-600 leading-relaxed">
            EarnAura reserves the right to update these Terms of Service at any time. We will notify users of 
            significant changes via email or through the platform. Continued use of the service after changes 
            constitutes acceptance of the updated terms.
          </p>
        </div>
      </section>
    </div>

    <div className="border-t pt-6 text-center">
      <p className="text-gray-600 mb-4">Questions about these terms?</p>
      <a href="mailto:tortoor8@gmail.com?subject=Terms%20of%20Service%20Question" className="text-[#00CC7E] hover:text-[#00BB70] font-medium">
        Contact us at tortoor8@gmail.com
      </a>
    </div>
  </div>
);

export { FooterModal, AboutUsContent, PrivacyContent, SupportContent, TermsContent };
