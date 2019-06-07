Thank you for considering working with us! The Data Science team at AstraZeneca work on many diverse problems across the company, pushing the boundaries of science to deliver life-changing medicines.

The aim of the exercise is to give you an idea of the range of work you could be doing as part of our team. The problem is intentionally small in scope and size and is not likely to move you closer to a successful medicine. Instead, it touches on a variety of skills we’d be expected to apply: analyse problems, gather data, explore, visualise, transform and use this data to predict.

We are interested to see:

- how you analyse and structure a problem,
- how fluent you are with your programming language of choice and
- how familiar you are with development tools.

We are not so interested in how far you get, but rather on your coding style and how you approach the problem. 

Details:

You have 3 days to complete the exercise, however **you should not spend more than 2 hours** on it from beginning to end. 

You can choose to use python, Scala or R.

Use available libraries when you can - rewriting tools from scratch will not be rewarded.

We will not offer any assistance or clarification during the coding exercise. If you have any questions, simply state your assumptions and continue working.

Please send back your solution via email, in whichever format you prefer.

## Part A

Using the data from the OpenFDA API (documentation at [https://open.fda.gov/apis/drug/label/](https://open.fda.gov/apis/drug/label/)) to determine the average number of ingredients (`spl_product_data_elements`) contained in AstraZeneca medicines *per year*.

1. Choose a method to gather the data
2. Transform the data as you see fit
3. Visualize and explore the results

The output should look similar to:

    year   drug_names     avg_number_of_ingredients
    2018   drugA,drugB    21
    ... 

## Part B

Repeat the same analysis, calculate the average number of ingredients *per year and per delivery route* for all manufacturers. 

The output should look similar to:

    year   route      avg_number_of_ingredients
    2018   oral       123
    2018   injection  213
    2017   ...        ...
    ...

## Optional

Below are some questions to explore this toy problem further. Try creating some code if you still have time, or we can discuss some of these if you are invited for later stages of the interview:

- How would you code a model to predict the number of ingredients for next year?
  *Note: Your predictions don't have to be good !*
- Could you find the most common drug interactions for AstraZeneca medicines?
- How would you deploy your analysis/model as a tool that other users can use?