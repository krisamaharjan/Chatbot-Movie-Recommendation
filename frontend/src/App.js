import logo from './logo.svg';
import './App.css';
import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Box, TextField, Button, List, ListItem, ListItemText, Paper, Typography } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    // Add user message
    const userMessage = { text: input, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    setInput('');

    try {
      // Call Django backend
      const formData = new FormData();
      formData.append('query', input);
      
      const response = await axios.post('http://localhost:8000/recommend/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Add bot response
      const botMessage = { text: response.data.response, sender: 'bot' };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = { text: "Sorry, I couldn't process your request.", sender: 'bot' };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  return (
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height: '100vh',
      maxWidth: '800px',
      margin: '0 auto',
      padding: 2
    }}>
      <Typography variant="h4" gutterBottom sx={{ textAlign: 'center', mb: 2 }}>
        Movie Recommendation Bot
      </Typography>
      
      <Paper elevation={3} sx={{ flexGrow: 1, overflow: 'auto', mb: 2 }}>
        <List>
          {messages.map((msg, index) => (
            <ListItem key={index} sx={{ 
              justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start'
            }}>
              <ListItemText
                primary={msg.text}
                sx={{
                  p: 1,
                  borderRadius: 2,
                  bgcolor: msg.sender === 'user' ? '#1976d2' : '#e0e0e0',
                  color: msg.sender === 'user' ? 'white' : 'black',
                  maxWidth: '70%',
                  wordBreak: 'break-word'
                }}
              />
            </ListItem>
          ))}
          <div ref={messagesEndRef} />
        </List>
      </Paper>

      <Box sx={{ display: 'flex', gap: 1 }}>
        <TextField
          fullWidth
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask for movie recommendations..."
        />
        <Button 
          variant="contained" 
          onClick={handleSend}
          endIcon={<SendIcon />}
        >
          Send
        </Button>
      </Box>
    </Box>

  );
}

export default App;
