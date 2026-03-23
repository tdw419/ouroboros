 DECISION: PIVOT root                                         
 H: The `generate_tests.py` script is syntactically broken   
    (triple quotes in docstrings) and logically incomplete.  
    To increase coverage, we first need a working test       
    generation script that can parse the AST and produce     
    valid Python test files. We will fix syntax, complete    
    the generation logic, and execute it to create tests.    
 T: generate_tests.py                                        
 M: Script exits without error, produces a valid .py file.   
 B: 30 seconds                                               
 FLOW: HYP → RUN → EVAL → DECIDE                             