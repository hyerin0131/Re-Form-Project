import React, {useState} from 'react';
import { TextField, Button, Box } from "@material-ui/core";
import { makeStyles } from "@material-ui/core/styles";

const useStyles = makeStyles((theme) => ({
    root: {
      display: 'flex',
      flexWrap: 'wrap',
    },
    textField: {
      marginLeft: theme.spacing(1),
      marginRight: theme.spacing(1),
      // width: '25',
    },
    inputText: {
        color: 'rgba(0,0,0,0.87)',
        fontSize: '24px',
        letterSpacing: '0.5px',
        lineHeight: '28px',
        textAlign: 'center',
    },
}));

export default function InputBox(){

    const classes = useStyles();

    const [inputData, setInputData] = useState("");
    const [showResult, setShowResult] = useState(false);
    const [result, setResult] = useState("");

    const submitHandler = () => {
      console.log(inputData);
      setShowResult(true);
      setResult("translated:"+inputData);
      return;
    }
    const inputHandler = event => {
      // console.log(event.target.value);
      setInputData(event.target.value);
      // console.log(inputData)
    }

    return(
        <div className={classes.root}>
            <Box component="span" width="100%" border={1} borderRadius="borderRadius" borderColor={{color:'grey'}}>
                <TextField 
                    label="Input Your Text"
                    className={classes.textField}
                    style={{ margin: 8 }}
                    margin="normal"
                    fullWidth
                    InputLabelProps={{className: classes.inputText, style: {color: 'grey'}}}
                    inputProps={{min: 0, style: { textAlign: 'center'}}}
                    InputProps={{className: classes.inputText}}
                    variant="outlined"
                />
                <Button color="primary">Reconjugate</Button>
            </Box>
        </div>
    )
}