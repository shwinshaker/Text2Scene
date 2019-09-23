import React, { Component } from 'react';
import './App.css';
import Container from 'react-bootstrap/Container';
import 'bootstrap/dist/css/bootstrap.css';
import {Caption, BodyImage, BodyCorrection} from './content';
import BodyForm from './Form';

class App extends Component {

  constructor(props) {
    super(props);

    this.state = {
      isLoading: false,
      formData: {
        text: "A boy sits on the chari and plasy games at home."
      },
      path: "", //[],
      corrections: "",
      error: ""
    };
  }

  handleChange = (event) => {
    const value = event.target.value;
    const name = event.target.name;
    var formData = this.state.formData;
    formData[name] = value;
    this.setState({
      formData
    });
  }

  handlePredictClick = (event) => {
    const formData = this.state.formData;
    this.setState({ isLoading: true });
    fetch('http://127.0.0.1:5000/prediction/', 
      {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        method: 'POST',
        body: JSON.stringify(formData)
      })
      .then(response => 
        response.json()
      )
      .then(response => {
        console.log(response)
        this.setState({
          path: response.path,
          corrections: response.corrections,
          isLoading: false,
      });
    });
  }

  handleCancelClick = (event) => {
    this.setState({ path: "" });
  }

  handleSuggestionClick = (id, suggestion) => {
    var formData = this.state.formData;
    var arr = formData.text.split(/\s+/);
    arr[id] = suggestion;
    console.log([id, suggestion]);
    const text = arr.join(' ');
    formData.text = text;
    this.setState({formData: formData});
  }

  render() {
    const isLoading = this.state.isLoading;
    const formData = this.state.formData;
    const path = this.state.path;
    const corrections = this.state.corrections;

    return (
      <Container>
        <div>
          <Caption/>
        </div>
        <div className="content" id="content">
          <BodyForm
            formData = {formData}
            isLoading = {isLoading}
            handleChange = {this.handleChange}
            handlePredictClick = {this.handlePredictClick}
            handleCancelClick = {this.handleCancelClick}
          />
          <BodyCorrection
            corrections = {corrections}
            handleSuggestionClick = {this.handleSuggestionClick}
          />
          <BodyImage
            path = {path}
            isLoading = {isLoading}
          />
        </div>
      </Container>
    );
  }
}

export default App;