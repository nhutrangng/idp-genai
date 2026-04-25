const express=require('express');
const app=express();
const port=8080;
app.get('/',(req,res) => {
    res.send('Hello! This is my first service using Backstage template');
});
app.listen(port,()=>{
    console.log(`IDP GenAI is running on port http://localhost:${port}`);
});