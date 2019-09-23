import React, { Component } from 'react';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import logo from './logo.svg'
import Image from 'react-bootstrap/Image';
import Container from 'react-bootstrap/Container';

export class Result extends Component {

    render() {
        if (this.props.result) {
            return (
                <Row>
                  <Col className="result-container">
                    <h5 id="result">{this.props.result}</h5>
                  </Col>
                </Row>
               )
        }
        return null

    }
}

export class Caption extends Component {
    render() {
        // return <h3 className="title">Iris Plant Classifier</h3>
        return <h1 className="title">Text2Scene</h1>
    }
}

export class BodyCorrection extends Component {

    makeSuggestion(id, suggestions) {
        if (suggestions.length === 0 ) { return null }
        var wlist = [<span key='head'> Did you mean</span>];
        for (var i=0; i<suggestions.length; i++) {
            const sugg = suggestions[i];
            wlist.push(<span
                         id='suggest-word'
                         onClick={() => this.props.handleSuggestionClick(id, sugg)}
                         key={i}> {sugg}</span>);
        }
        wlist.push(<span key='tail'>?</span>)
        return wlist
    }

    render() {
        if (!this.props.corrections) {return null}
        const corrections = this.props.corrections;
        // const spanClick = 
        var plists = [];
        for (let key in corrections) {
            plists.push(
                <Row key={key}>
                    <p className='p'>
                        Out-of-vocabulary word
                        <span id='word'> {key} </span>
                        detected!
                        {this.makeSuggestion(corrections[key]['id'],
                                             corrections[key]['suggestions'])}
                        {/* {corrections[key]['suggestions'].length > 0 ? corrections[key]['id'] : null} */}
                    </p>
                </Row>
            )
        }
        return (<Container> <div className='word-container'> {plists} </div> </Container>)
    }
}

export class BodyImage extends Component {
    render() {
        if (!this.props.path) {
            // const className = this.props.isLoading ? "App-logo-spin" : "App-logo"
            if (this.props.isLoading){
                return (
                    <Image
                        src={logo}
                        alt="Logo"
                        className= "App-logo-spin"
                        // {/*className*/} 
                        fluid
                  />
                )
            }
            return null
        }
        else {
            var cols = []
            for (var i=1; i<this.props.path.length; i++) {
                cols.push(
                    <Col className='Col' key={i}>
                        <Image
                            src={this.props.path[i]}
                            alt='image'
                            className="App-logo-small"
                            fluid
                        />
                    </Col>
                )
            }
            return (
                <Container>
                    <Row>
                        <Image
                            src={this.props.path[0]}
                            alt='image'
                            className="App-logo"
                            fluid
                        />
                    </Row>
                    <Row>
                        {cols}
                    </Row>
                    {/* <Row>
                        <BarChart/>
                    </Row> */}
                </Container>
            )
        }
    }
}
