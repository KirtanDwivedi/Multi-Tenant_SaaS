import { X, Mail } from 'lucide-react';

export default function LoginModal({ close, setUserName }) {
  const handleFakeLogin = () => {
    setUserName("Kirtan"); // Simulating JWT success
    close();
  };

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="bg-[#212121] w-full max-w-[400px] rounded-2xl p-8 relative border border-white/10">
        <button onClick={close} className="absolute top-4 right-4 text-gray-500 hover:text-white"><X size={20}/></button>
        <h2 className="text-2xl font-bold text-center mb-2">Log in or sign up</h2>
        <p className="text-sm text-gray-400 text-center mb-8">You'll get smarter responses and can upload files, images, and more.</p>
        
        <div className="space-y-3">
          <button onClick={handleFakeLogin} className="w-full flex items-center justify-center gap-3 border border-white/20 py-3 rounded-xl hover:bg-white/5 transition">
            <img src="https://www.google.com/favicon.ico" className="w-4 h-4" alt="G" /> Continue with Google
          </button>
          <button className="w-full flex items-center justify-center gap-3 border border-white/20 py-3 rounded-xl hover:bg-white/5 transition">
            <span className="text-xl"></span> Continue with Apple
          </button>
          
          <div className="relative py-4">
            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-white/10"></div></div>
            <div className="relative flex justify-center text-xs uppercase"><span className="bg-[#212121] px-2 text-gray-500">OR</span></div>
          </div>

          <input type="email" placeholder="Email address" className="w-full bg-[#303030] border border-white/10 p-3 rounded-xl outline-none focus:ring-1 ring-white/30" />
          <button className="w-full bg-white text-black font-bold py-3 rounded-xl hover:bg-gray-200">Continue</button>
        </div>
      </div>
    </div>
  );
}