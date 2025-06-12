import React, { useState, useEffect } from 'react';
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Welcome Screen Component
const WelcomeScreen = ({ onStart }) => {
  return (
    <div className="welcome-screen">
      <div className="welcome-content">
        <div className="party-icon">🎉</div>
        <h1 className="welcome-title">Let's Plan Your Party</h1>
        <p className="welcome-subtitle">
          Calculate exactly how much alcohol and mixers you need based on your guest count and party vibe!
        </p>
        <button className="start-button" onClick={onStart}>
          Start Planning
        </button>
      </div>
    </div>
  );
};

// Input Form Component
const InputForm = ({ formData, setFormData, onNext }) => {
  const [guests, setGuests] = useState(formData.guests || 8);
  const [drinkerType, setDrinkerType] = useState(formData.drinkerType || 'medium');
  const [duration, setDuration] = useState(formData.duration || 4);

  const handleNext = () => {
    setFormData({ ...formData, guests, drinkerType, duration });
    onNext();
  };

  return (
    <div className="form-screen">
      <div className="form-content">
        <h2 className="form-title">Party Details</h2>
        
        <div className="form-section">
          <label className="form-label">Number of Guests</label>
          <div className="stepper">
            <button 
              className="stepper-btn"
              onClick={() => setGuests(Math.max(1, guests - 1))}
            >
              -
            </button>
            <span className="stepper-value">{guests}</span>
            <button 
              className="stepper-btn"
              onClick={() => setGuests(guests + 1)}
            >
              +
            </button>
          </div>
        </div>

        <div className="form-section">
          <label className="form-label">Drinking Intensity</label>
          <div className="radio-group">
            {[
              { id: 'light', label: 'Light Drinkers', desc: '1-2 drinks/hour' },
              { id: 'medium', label: 'Medium Drinkers', desc: '2-3 drinks/hour' },
              { id: 'heavy', label: 'Heavy Drinkers', desc: '3+ drinks/hour' }
            ].map(option => (
              <label key={option.id} className="radio-option">
                <input
                  type="radio"
                  name="drinkerType"
                  value={option.id}
                  checked={drinkerType === option.id}
                  onChange={(e) => setDrinkerType(e.target.value)}
                />
                <div className="radio-content">
                  <span className="radio-label">{option.label}</span>
                  <span className="radio-desc">{option.desc}</span>
                </div>
              </label>
            ))}
          </div>
        </div>

        <div className="form-section">
          <label className="form-label">Party Duration (hours)</label>
          <div className="stepper">
            <button 
              className="stepper-btn"
              onClick={() => setDuration(Math.max(1, duration - 1))}
            >
              -
            </button>
            <span className="stepper-value">{duration}h</span>
            <button 
              className="stepper-btn"
              onClick={() => setDuration(duration + 1)}
            >
              +
            </button>
          </div>
        </div>

        <button className="next-button" onClick={handleNext}>
          Choose Drinks →
        </button>
      </div>
    </div>
  );
};

// Drink Selection Component
const DrinkSelection = ({ formData, setFormData, onNext }) => {
  const [drinkTypes, setDrinkTypes] = useState(formData.drinkTypes || ['beer', 'wine']);
  const [mixers, setMixers] = useState(formData.mixers || []);
  const [showMixers, setShowMixers] = useState(false);

  const drinks = [
    { id: 'beer', name: 'Beer', icon: '🍺' },
    { id: 'wine', name: 'Wine', icon: '🍷' },
    { id: 'vodka', name: 'Vodka', icon: '🥃' },
    { id: 'whiskey', name: 'Whiskey', icon: '🥃' },
    { id: 'rum', name: 'Rum', icon: '🥃' },
    { id: 'gin', name: 'Gin', icon: '🍸' }
  ];

  const mixerOptions = [
    { id: 'soda', name: 'Soda' },
    { id: 'juice', name: 'Juice' },
    { id: 'tonic', name: 'Tonic Water' }
  ];

  const toggleDrink = (drinkId) => {
    const newTypes = drinkTypes.includes(drinkId)
      ? drinkTypes.filter(id => id !== drinkId)
      : [...drinkTypes, drinkId];
    setDrinkTypes(newTypes);
    
    // Auto-show mixers if spirits are selected
    const spirits = ['vodka', 'whiskey', 'rum', 'gin'];
    const hasSpirits = newTypes.some(drink => spirits.includes(drink));
    setShowMixers(hasSpirits);
  };

  const toggleMixer = (mixerId) => {
    const newMixers = mixers.includes(mixerId)
      ? mixers.filter(id => id !== mixerId)
      : [...mixers, mixerId];
    setMixers(newMixers);
  };

  const handleNext = () => {
    setFormData({ ...formData, drinkTypes, mixers });
    onNext();
  };

  return (
    <div className="form-screen">
      <div className="form-content">
        <h2 className="form-title">Choose Your Drinks</h2>
        
        <div className="form-section">
          <label className="form-label">Select Drink Types</label>
          <div className="chip-grid">
            {drinks.map(drink => (
              <button
                key={drink.id}
                className={`drink-chip ${drinkTypes.includes(drink.id) ? 'selected' : ''}`}
                onClick={() => toggleDrink(drink.id)}
              >
                <span className="drink-icon">{drink.icon}</span>
                <span className="drink-name">{drink.name}</span>
              </button>
            ))}
          </div>
        </div>

        {showMixers && (
          <div className="form-section">
            <label className="form-label">Add Mixers (Optional)</label>
            <div className="chip-grid">
              {mixerOptions.map(mixer => (
                <button
                  key={mixer.id}
                  className={`mixer-chip ${mixers.includes(mixer.id) ? 'selected' : ''}`}
                  onClick={() => toggleMixer(mixer.id)}
                >
                  {mixer.name}
                </button>
              ))}
            </div>
          </div>
        )}

        <button 
          className="next-button" 
          onClick={handleNext}
          disabled={drinkTypes.length === 0}
        >
          Calculate My Party →
        </button>
      </div>
    </div>
  );
};

// Results Component
const ResultsScreen = ({ formData, onReset }) => {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const calculateResults = async () => {
      try {
        setLoading(true);
        const response = await axios.post(`${API}/calculate`, {
          guests: formData.guests,
          drinker_type: formData.drinkerType,
          duration: formData.duration,
          drink_types: formData.drinkTypes,
          mixers: formData.mixers || []
        });
        setResults(response.data);
      } catch (err) {
        console.error('Calculation error:', err);
        setError('Failed to calculate party needs. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    calculateResults();
  }, [formData]);

  const shareResults = () => {
    if (!results) return;
    
    const shareText = `🎉 Party Planning Results!\n\n` +
      `For ${formData.guests} ${formData.drinkerType} drinkers (${formData.duration}h party):\n\n` +
      `Drinks needed:\n${results.drinks.map(d => `• ${d.amount} ${d.unit} of ${d.drink_type}`).join('\n')}\n\n` +
      `${results.mixers.length > 0 ? `Mixers:\n${results.mixers.map(m => `• ${m.amount} ${m.unit} of ${m.drink_type}`).join('\n')}\n\n` : ''}` +
      `Extras:\n${results.extras.map(e => `• ${e.amount} ${e.unit} ${e.drink_type}`).join('\n')}\n\n` +
      `Estimated cost: $${results.total_cost_estimate}\n\n` +
      `${results.fun_message}`;

    if (navigator.share) {
      navigator.share({
        title: 'Party Drink Calculator Results',
        text: shareText
      });
    } else {
      navigator.clipboard.writeText(shareText);
      alert('Results copied to clipboard!');
    }
  };

  if (loading) {
    return (
      <div className="results-screen">
        <div className="results-content">
          <div className="loading">
            <div className="loading-icon">🎉</div>
            <p>Calculating your perfect party...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="results-screen">
        <div className="results-content">
          <div className="error">
            <h2>Oops! Something went wrong</h2>
            <p>{error}</p>
            <button className="reset-button" onClick={onReset}>
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="results-screen">
      <div className="results-content">
        <div className="results-header">
          <h2 className="results-title">Your Party Plan is Ready! 🎉</h2>
          <p className="fun-message">{results.fun_message}</p>
        </div>

        <div className="results-sections">
          <div className="result-section">
            <h3 className="section-title">🍻 Drinks</h3>
            {results.drinks.map((drink, index) => (
              <div key={index} className="result-item">
                <div className="item-main">
                  <span className="item-amount">{drink.amount} {drink.unit}</span>
                  <span className="item-name">{drink.drink_type}</span>
                </div>
                <p className="item-desc">{drink.description}</p>
              </div>
            ))}
          </div>

          {results.mixers.length > 0 && (
            <div className="result-section">
              <h3 className="section-title">🥤 Mixers</h3>
              {results.mixers.map((mixer, index) => (
                <div key={index} className="result-item">
                  <div className="item-main">
                    <span className="item-amount">{mixer.amount} {mixer.unit}</span>
                    <span className="item-name">{mixer.drink_type}</span>
                  </div>
                  <p className="item-desc">{mixer.description}</p>
                </div>
              ))}
            </div>
          )}

          <div className="result-section">
            <h3 className="section-title">🧊 Extras</h3>
            {results.extras.map((extra, index) => (
              <div key={index} className="result-item">
                <div className="item-main">
                  <span className="item-amount">{extra.amount} {extra.unit}</span>
                  <span className="item-name">{extra.drink_type}</span>
                </div>
                <p className="item-desc">{extra.description}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="results-footer">
          <div className="cost-estimate">
            <strong>Estimated Total Cost: ${results.total_cost_estimate}</strong>
          </div>
          
          <div className="action-buttons">
            <button className="share-button" onClick={shareResults}>
              Share Plan 📤
            </button>
            <button className="reset-button" onClick={onReset}>
              Plan Another Party
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [currentScreen, setCurrentScreen] = useState('welcome');
  const [formData, setFormData] = useState({});

  const handleStart = () => setCurrentScreen('input');
  const handleInputNext = () => setCurrentScreen('selection');
  const handleSelectionNext = () => setCurrentScreen('results');
  const handleReset = () => {
    setCurrentScreen('welcome');
    setFormData({});
  };

  // Test API connection
  useEffect(() => {
    const testConnection = async () => {
      try {
        const response = await axios.get(`${API}/`);
        console.log('✅ API Connected:', response.data.message);
      } catch (error) {
        console.error('❌ API Connection Failed:', error);
      }
    };
    testConnection();
  }, []);

  return (
    <div className="app">
      {currentScreen === 'welcome' && <WelcomeScreen onStart={handleStart} />}
      {currentScreen === 'input' && (
        <InputForm 
          formData={formData} 
          setFormData={setFormData} 
          onNext={handleInputNext} 
        />
      )}
      {currentScreen === 'selection' && (
        <DrinkSelection 
          formData={formData} 
          setFormData={setFormData} 
          onNext={handleSelectionNext} 
        />
      )}
      {currentScreen === 'results' && (
        <ResultsScreen 
          formData={formData} 
          onReset={handleReset} 
        />
      )}
    </div>
  );
}

export default App;