import React, { Component } from "react";
import axios from "axios";
import InputBox from './Components/InputBox';
import OutputBox from './Components/OutputBox';

class App extends Component{
  render(){
    return (
      <>
        <InputBox />
        <OutputBox />
      </>
    );
  }
}

export default App;
