import React, { useState } from 'react';
import { 
  EnvelopeIcon, 
  HeartIcon
} from '@heroicons/react/24/outline';
import { FooterModal, AboutUsContent, PrivacyContent, SupportContent, TermsContent } from './FooterModel';

const Footer = () => {
  const currentYear = new Date().getFullYear();
  const [modalContent, setModalContent] = useState(null);
  const [modalTitle, setModalTitle] = useState('');
  
  const openModal = (content, title) => {
    setModalContent(content);
    setModalTitle(title);
  };

  const closeModal = () => {
    setModalContent(null);
    setModalTitle('');
  };

  const quickLinks = [
    { 
      name: 'About Us', 
      onClick: () => openModal(<AboutUsContent />, 'About EarnAura')
    },
    { 
      name: 'Support', 
      onClick: () => openModal(<SupportContent />, 'Support Center')
    },
    { 
      name: 'Privacy', 
      onClick: () => openModal(<PrivacyContent />, 'Privacy Policy')
    },
    { 
      name: 'Terms', 
      onClick: () => openModal(<TermsContent />, 'Terms of Service')
    }
  ];

  return (
    <>
      <footer className="bg-gray-900 text-white py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Main Footer Content */}
          <div className="grid md:grid-cols-3 gap-8 mb-6">
            {/* Brand Section */}
            <div>
              <div className="flex items-center mb-4">
                <div className="w-8 h-8 bg-[#00CC7E] rounded-lg flex items-center justify-center mr-2">
                  <span className="text-white text-lg font-bold">₹</span>
                </div>
                <h3 className="text-xl font-bold text-[#00CC7E]">
                  EarnAura
                </h3>
              </div>
              <p className="text-gray-300 text-sm mb-3">
                Your trusted companion for financial success and wealth building.
              </p>
              <div className="flex items-center text-gray-300 text-sm">
                <EnvelopeIcon className="w-4 h-4 mr-2 text-[#00CC7E]" />
                <a href="mailto:tortoor8@gmail.com" className="hover:text-[#00CC7E] transition-colors">
                  tortoor8@gmail.com
                </a>
              </div>
            </div>

            {/* Quick Links */}
            <div>
              <h4 className="text-lg font-semibold mb-4 text-[#00CC7E]">Quick Links</h4>
              <div className="grid grid-cols-2 gap-2">
                {quickLinks.map((link, index) => (
                  <button
                    key={index}
                    onClick={link.onClick}
                    className="text-gray-300 hover:text-white transition-colors text-sm text-left"
                  >
                    {link.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Contact Support */}
            <div>
              <h4 className="text-lg font-semibold mb-4 text-[#00CC7E]">Need Help?</h4>
              <a 
                href="mailto:tortoor8@gmail.com?subject=EarnAura%20Support%20Request"
                className="inline-flex items-center px-4 py-2 bg-[#00CC7E] hover:bg-[#00BB70] text-white rounded-lg transition-colors text-sm font-medium"
              >
                <EnvelopeIcon className="w-4 h-4 mr-2" />
                Contact Support
              </a>
            </div>
          </div>

          {/* Bottom Section */}
          <div className="border-t border-gray-800 pt-6">
            <div className="flex flex-col sm:flex-row justify-between items-center">
              <div className="flex items-center mb-4 sm:mb-0">
                <p className="text-gray-400 text-sm">
                  © {currentYear} EarnAura. All rights reserved.
                </p>
                <div className="flex items-center ml-4">
                  <span className="text-gray-400 text-sm">Made with</span>
                  <HeartIcon className="w-4 h-4 text-red-500 mx-1" />
                  <span className="text-gray-400 text-sm">for financial empowerment</span>
                </div>
              </div>
              
              <div className="text-gray-400 text-xs">
                Secure • Private • Trusted
              </div>
            </div>
          </div>
        </div>
      </footer>

      {/* Modal */}
      <FooterModal 
        isOpen={!!modalContent} 
        onClose={closeModal} 
        title={modalTitle}
      >
        {modalContent}
      </FooterModal>
    </>
  );
};

export default Footer;
