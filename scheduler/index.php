

<script> 
    var currentDay = 'Sunday';
    var nextSunday = 'Sun, 30 Apr 2023';
    var habits = ["Hygiene","Oraganize your life","Planning","Eat Healthy","Drink Water","Learn New Stuff","Sport","Take Fresh air","Reading","Quit Bad Habits","Sleep 8 hours"];
    var habitsLenth = '11';
    var days = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];
    var defaultGoals = ["Electricity","","Maths","Electricity","Data structure","","Portswigger","HackTheBox","eJPT","","Project","","Data base","eJPT"];
    var defaultHours = ["3","8","2","4","8","8","8"];
</script>

       
<!DOCTYPE html>
<html lang="en" data-theme="" style="--main-color :#212529">
<head>
    <meta charset="UTF-8">
    <meta meta name="viewport" content="width=device-width", initial-scale="1", maximum-scale="1", user-scalable="no">    
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
    <link href="css/1.css"  rel="stylesheet">
    <link href="css/2.css"  rel="stylesheet">
    <link href="css/3.css"  rel="stylesheet">
    <link href="css/all.min.css"  rel="stylesheet">
    <title>Scheduling</title> 
</head>
<body>

    <a class="navbar-brand" id="home" href="index.php" >Home</a>

    <div class="form-check form-switch" >
        <input class="form-check-input" type="checkbox" value="Dark"  id="themeSwitch" onclick="theme()" >
        <label class="form-check-label" for="themeSwitch" >Dark Theme</label>
    </div>
    

    <button type="button" id="defaultValuesBtn" onclick='defaultValuesFunction()'> Default Values </button>

    <input type="color" class="form-control form-control-color" id="colorChanger" value=#212529 title="Choose your color">

    <br>
    
    <table class="table" id="mainTable">
        <thead class="table table-bordered border-end border-start">
            <tr>
                <th></th>
                <th id="day">Day</th>
                <th id="date">Date</th>
                <th id="hours" >Hours</th>
                <th id="goals">Goals</th>
                <th id="habits"></th>
                <th id="submit"></th>
                <th></th>
            </tr>
        </thead>
        <tbody>
            
       
            
                        
                            

                                <tr>

                                        <td> <i class="fa-solid fa-caret-right" id=currentDay0></i> </td>
                                    
                            

                                        <td class="days" id=day0 >Sunday</td>

                                                                                        <td class="dates" id=date0 > 23/04/23 </td>
                                               

                                                
                                        

                                        <td class='hours' > <input type='range' class='form-range js-hours-range-input' min='0' max='8' id=ran0 > </td>
                                    
                                        

                                                        
                                                    
                                                
                                            

                                        <td class="goals">

                                            
                                                <table class="table table-borderless">
                                                                            
                                                        <td id=g0 > </td>
                                                        <td id=g1 ></td>                    
                                                    
                                                </table>
                                           
                                        </td>

                                        <td class="ha">
                                            <i class="fa-solid fa-dumbbell" id=hab0 onclick='habitsFunction(id)'></i>
                                        </td>
                                    
                                        
                                        <td>
                                            <button type="button" id=sub0 class="submit-btn js-first-submit-btns"  data-sub="submit0" onclick='summeryFunction(id)' title="sfdgsdgdfhfgdhfgbdhfghddhgdg"> Submit </button>
                                                    
                                        </td>
                                       
                                        <td>      
                                            <div id="emailHelp" class="form-text">3</div>
                                        </td>
                                  
                                </tr>
                            
                        
                        
                        
                            

                                <tr>

                                        <td> <i class="fa-solid fa-caret-right" id=currentDay1></i> </td>
                                    
                            

                                        <td class="days" id=day1 >Monday</td>

                                                                                        <td class="dates" id=date1 > 23/04/24 </td>
                                               

                                                
                                        

                                        <td class='hours' > <input type='range' class='form-range js-hours-range-input' min='0' max='8' id=ran1 > </td>
                                    
                                        

                                                        
                                                    
                                                
                                            

                                        <td class="goals">

                                            
                                                <table class="table table-borderless">
                                                                            
                                                        <td id=g2 > </td>
                                                        <td id=g3 ></td>                    
                                                    
                                                </table>
                                           
                                        </td>

                                        <td class="ha">
                                            <i class="fa-solid fa-dumbbell" id=hab1 onclick='habitsFunction(id)'></i>
                                        </td>
                                    
                                        
                                        <td>
                                            <button type="button" id=sub1 class="submit-btn js-first-submit-btns"  data-sub="submit0" onclick='summeryFunction(id)' title="sfdgsdgdfhfgdhfgbdhfghddhgdg"> Submit </button>
                                                    
                                        </td>
                                       
                                        <td>      
                                            <div id="emailHelp" class="form-text">8</div>
                                        </td>
                                  
                                </tr>
                            
                        
                        
                        
                            

                                <tr>

                                        <td> <i class="fa-solid fa-caret-right" id=currentDay2></i> </td>
                                    
                            

                                        <td class="days" id=day2 >Tuesday</td>

                                                                                        <td class="dates" id=date2 > 23/04/25 </td>
                                               

                                                
                                        

                                        <td class='hours' > <input type='range' class='form-range js-hours-range-input' min='0' max='8' id=ran2 > </td>
                                    
                                        

                                                        
                                                    
                                                
                                            

                                        <td class="goals">

                                            
                                                <table class="table table-borderless">
                                                                            
                                                        <td id=g4 > </td>
                                                        <td id=g5 ></td>                    
                                                    
                                                </table>
                                           
                                        </td>

                                        <td class="ha">
                                            <i class="fa-solid fa-dumbbell" id=hab2 onclick='habitsFunction(id)'></i>
                                        </td>
                                    
                                        
                                        <td>
                                            <button type="button" id=sub2 class="submit-btn js-first-submit-btns"  data-sub="submit0" onclick='summeryFunction(id)' title="sfdgsdgdfhfgdhfgbdhfghddhgdg"> Submit </button>
                                                    
                                        </td>
                                       
                                        <td>      
                                            <div id="emailHelp" class="form-text">2</div>
                                        </td>
                                  
                                </tr>
                            
                        
                        
                        
                            

                                <tr>

                                        <td> <i class="fa-solid fa-caret-right" id=currentDay3></i> </td>
                                    
                            

                                        <td class="days" id=day3 >Wednesday</td>

                                                                                        <td class="dates" id=date3 > 23/04/26 </td>
                                               

                                                
                                        

                                        <td class='hours' > <input type='range' class='form-range js-hours-range-input' min='0' max='8' id=ran3 > </td>
                                    
                                        

                                                        
                                                    
                                                
                                            

                                        <td class="goals">

                                            
                                                <table class="table table-borderless">
                                                                            
                                                        <td id=g6 > </td>
                                                        <td id=g7 ></td>                    
                                                    
                                                </table>
                                           
                                        </td>

                                        <td class="ha">
                                            <i class="fa-solid fa-dumbbell" id=hab3 onclick='habitsFunction(id)'></i>
                                        </td>
                                    
                                        
                                        <td>
                                            <button type="button" id=sub3 class="submit-btn js-first-submit-btns"  data-sub="submit0" onclick='summeryFunction(id)' title="sfdgsdgdfhfgdhfgbdhfghddhgdg"> Submit </button>
                                                    
                                        </td>
                                       
                                        <td>      
                                            <div id="emailHelp" class="form-text">4</div>
                                        </td>
                                  
                                </tr>
                            
                        
                        
                        
                            

                                <tr>

                                        <td> <i class="fa-solid fa-caret-right" id=currentDay4></i> </td>
                                    
                            

                                        <td class="days" id=day4 >Thursday</td>

                                                                                        <td class="dates" id=date4 > 23/04/27 </td>
                                               

                                                
                                        

                                        <td class='hours' > <input type='range' class='form-range js-hours-range-input' min='0' max='8' id=ran4 > </td>
                                    
                                        

                                                        
                                                    
                                                
                                            

                                        <td class="goals">

                                            
                                                <table class="table table-borderless">
                                                                            
                                                        <td id=g8 > </td>
                                                        <td id=g9 ></td>                    
                                                    
                                                </table>
                                           
                                        </td>

                                        <td class="ha">
                                            <i class="fa-solid fa-dumbbell" id=hab4 onclick='habitsFunction(id)'></i>
                                        </td>
                                    
                                        
                                        <td>
                                            <button type="button" id=sub4 class="submit-btn js-first-submit-btns"  data-sub="submit0" onclick='summeryFunction(id)' title="sfdgsdgdfhfgdhfgbdhfghddhgdg"> Submit </button>
                                                    
                                        </td>
                                       
                                        <td>      
                                            <div id="emailHelp" class="form-text">8</div>
                                        </td>
                                  
                                </tr>
                            
                        
                        
                        
                            

                                <tr>

                                        <td> <i class="fa-solid fa-caret-right" id=currentDay5></i> </td>
                                    
                            

                                        <td class="days" id=day5 >Friday</td>

                                                                                        <td class="dates" id=date5 > 23/04/28 </td>
                                               

                                                
                                        

                                        <td class='hours' > <input type='range' class='form-range js-hours-range-input' min='0' max='8' id=ran5 > </td>
                                    
                                        

                                                        
                                                    
                                                
                                            

                                        <td class="goals">

                                            
                                                <table class="table table-borderless">
                                                                            
                                                        <td id=g10 > </td>
                                                        <td id=g11 ></td>                    
                                                    
                                                </table>
                                           
                                        </td>

                                        <td class="ha">
                                            <i class="fa-solid fa-dumbbell" id=hab5 onclick='habitsFunction(id)'></i>
                                        </td>
                                    
                                        
                                        <td>
                                            <button type="button" id=sub5 class="submit-btn js-first-submit-btns"  data-sub="submit0" onclick='summeryFunction(id)' title="sfdgsdgdfhfgdhfgbdhfghddhgdg"> Submit </button>
                                                    
                                        </td>
                                       
                                        <td>      
                                            <div id="emailHelp" class="form-text">8</div>
                                        </td>
                                  
                                </tr>
                            
                        
                        
                        
                            

                                <tr>

                                        <td> <i class="fa-solid fa-caret-right" id=currentDay6></i> </td>
                                    
                            

                                        <td class="days" id=day6 >Saturday</td>

                                                                                        <td class="dates" id=date6 > 23/04/29 </td>
                                               

                                                
                                        

                                        <td class='hours' > <input type='range' class='form-range js-hours-range-input' min='0' max='8' id=ran6 > </td>
                                    
                                        

                                                        
                                                    
                                                
                                            

                                        <td class="goals">

                                            
                                                <table class="table table-borderless">
                                                                            
                                                        <td id=g12 > </td>
                                                        <td id=g13 ></td>                    
                                                    
                                                </table>
                                           
                                        </td>

                                        <td class="ha">
                                            <i class="fa-solid fa-dumbbell" id=hab6 onclick='habitsFunction(id)'></i>
                                        </td>
                                    
                                        
                                        <td>
                                            <button type="button" id=sub6 class="submit-btn js-first-submit-btns"  data-sub="submit0" onclick='summeryFunction(id)' title="sfdgsdgdfhfgdhfgbdhfghddhgdg"> Submit </button>
                                                    
                                        </td>
                                       
                                        <td>      
                                            <div id="emailHelp" class="form-text">8</div>
                                        </td>
                                  
                                </tr>
                            
                        
                                    
        </tbody>
        
    </table>

    
<form method="post">
    <div id="stage">
            <div id="overlay"> </div>

            <div id="card">
                <h1 id="card-title"></h1> 
            </div>

            <div id="toggle-0"></div>
            <div id="toggle-1"></div>
    </div>
</form>

<div id="all-container">


    <div id="default-values-container">
        <form method="post" id="default-values-form">                
                <table class="table" id="default-values-table">
                        <thead class="table">
                            <tr>
                                <th id="dday">Day</th>
                                <th id="dhours" >Default Hours</th>
                                <th id="dgoals">Default Goals</th> 
                            </tr>
                        </thead>
                        <tbody>    
                            <td>    
                                <select class="form-select" id="day-select-list" name="selectedDay">
                                    <option value='0'>Choose day</option>
                                                                            <option id=option1 value=1 > Sunday </option>
                                                                                                                <option id=option2 value=2 > Monday </option>
                                                                                                                <option id=option3 value=3 > Tuesday </option>
                                                                                                                <option id=option4 value=4 > Wednesday </option>
                                                                                                                <option id=option5 value=5 > Thursday </option>
                                                                                                                <option id=option6 value=6 > Friday </option>
                                                                                                                <option id=option7 value=7 > Saturday </option>
                                                                            
                                </select>
                            </td>
                            <td>  <input name='defaultHour' type='range' class='form-range' min='0' max='8' id='dvr' > </td>
                            <td>
                                <table class="table table-borderless">
                                    <td> <input name='defaultGoal[]' type="text"  class="form-control" id="dv0" autocomplete='off'> </td>
                                    <td> <input name='defaultGoal[]' type="text"  class="form-control" id="dv1" autocomplete='off'> </td>
                                </table>
                            </td>
                        </tbody>
                </table> 
                <button type="button" id="default-values-changer">  Change </button>                
        </form>
    </div>




    <div id="habits-container">

        <table class="table" id="habits-table">
            <tbody>                   
                
                    <tr> 
                        <td> <i class='fa-solid fa-shower' title='' ></i> </td>
                        <td> Hygiene</td>
                        <td class="habits-data-cell js-habits-data-cell"></td>                                                                                               
                    </tr>

                
                    <tr> 
                        <td> <i class='fa-solid fa-layer-group' title='' ></i> </td>
                        <td> Oraganize your life</td>
                        <td class="habits-data-cell js-habits-data-cell"></td>                                                                                               
                    </tr>

                
                    <tr> 
                        <td> <i class='fa-solid fa-clipboard' title='' ></i> </td>
                        <td> Planning</td>
                        <td class="habits-data-cell js-habits-data-cell"></td>                                                                                               
                    </tr>

                
                    <tr> 
                        <td> <i class='fa-solid fa-apple-whole' title='' ></i> </td>
                        <td> Eat Healthy</td>
                        <td class="habits-data-cell js-habits-data-cell"></td>                                                                                               
                    </tr>

                
                    <tr> 
                        <td> <i class='fa-solid fa-glass-water' title='' ></i> </td>
                        <td> Drink Water</td>
                        <td class="habits-data-cell js-habits-data-cell"></td>                                                                                               
                    </tr>

                
                    <tr> 
                        <td> <i class='fa-solid fa-brain' title='' ></i> </td>
                        <td> Learn New Stuff</td>
                        <td class="habits-data-cell js-habits-data-cell"></td>                                                                                               
                    </tr>

                
                    <tr> 
                        <td> <i class='fa-solid fa-dumbbell' title='' ></i> </td>
                        <td> Sport</td>
                        <td class="habits-data-cell js-habits-data-cell"></td>                                                                                               
                    </tr>

                
                    <tr> 
                        <td> <i class='fa-solid fa-cloud-sun' title='' ></i> </td>
                        <td> Take Fresh air</td>
                        <td class="habits-data-cell js-habits-data-cell"></td>                                                                                               
                    </tr>

                
                    <tr> 
                        <td> <i class='fa-solid fa-book-open-reader' title='' ></i> </td>
                        <td> Reading</td>
                        <td class="habits-data-cell js-habits-data-cell"></td>                                                                                               
                    </tr>

                
                    <tr> 
                        <td> <i class='fa-solid fa-ban' title='' ></i> </td>
                        <td> Quit Bad Habits</td>
                        <td class="habits-data-cell js-habits-data-cell"></td>                                                                                               
                    </tr>

                
                    <tr> 
                        <td> <i class='fa-solid fa-bed' title='' ></i> </td>
                        <td> Sleep 8 hours</td>
                        <td class="habits-data-cell js-habits-data-cell"></td>                                                                                               
                    </tr>

                      
            </tbody>
        </table>

    </div>


    <div id="summary-container">
        <table class="table" id="summary-table">
            <thead class="table">
                <tr>
                    <th id="day-teble-header">Day</th>
                    <th id="date-table-header">Date</th>
                    <th id="hours-table-header" >Hours</th>
                    <th colspan="2" id="goals-table-header">Achieved Goals</th> 
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td id="day-text"></td>
                    <td id="date-text"></td>
                    <input type="text" id='date-submit' name="date" style="display:none" >
                    <td id="hours-text"></td>
                    <input type="text" id='hours-submit' name="hours" style="display:none" >       
                    <td id="goals-text-0" ></td>
                    <input type='text' id='goals-submit-0' name='goals[]' autocomplete='off' class='form-control' style="display:none" >   
                    <td id="goals-text-1" ></td>
                    <input type='text' id='goals-submit-1' name='goals[]' autocomplete='off' class='form-control' style="display:none" > 
                </tr>
            </tbody>
        </table>
        <button class="submit-btn js-second-submit-btn" > Submit </button>
    </div>

</div>

    <script type="text/javascript" src="js/functions.js"></script>
    <script type="text/javascript" src="js/goals.js"></script>
    <script type="text/javascript" src="js/variables.js"></script>                        
    <script type="text/javascript" src="js/hours.js"></script>
    <script type="text/javascript" src="js/elements.js"></script>
</body>
</html>




