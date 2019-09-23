import React, { Component } from 'react';
import Form from 'react-bootstrap/Form';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import Button from 'react-bootstrap/Button';

export default class BodyForm extends Component {

    render() {

        const isLoading = this.props.isLoading;
        const text = this.props.formData.text;
        const handleChange = this.props.handleChange;
        const handlePredictClick = this.props.handlePredictClick;
        const handleCancelClick = this.props.handleCancelClick;

        return (
            <Form>
            <Form.Row>
              <Form.Group as={Col}>
                {/* <Form.Label>Text</Form.Label> */}
                <Form.Control
                  as="textarea"
                  name="text"
                  rows="3"
                  placeholder='Enter text..'
                  onChange={handleChange}
                  value={text}
                >
                 {/* {formData.text} ? formData.text : "example"} */}
                </Form.Control>
              </Form.Group>
            </Form.Row>
            <Row>
              <Col>
                <Button
                  block
                  variant="success"
                  disabled={isLoading}
                  onClick={!isLoading ? handlePredictClick : null}>
                  { isLoading ? 'Generating..' : 'Generate' }
                </Button>
              </Col>
              <Col>
                <Button
                  block
                  variant="danger"
                  disabled={isLoading}
                  onClick={handleCancelClick}>
                  Reset
                </Button>
              </Col>
            </Row>
          </Form>
        )
    }
}
