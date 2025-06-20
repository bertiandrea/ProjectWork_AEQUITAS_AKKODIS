Fairness Pipeline Documentation
===============================
Akkodis is a global company that provides consulting services and offers recruiting and training services. Since 2022, it has been part of the Adecco Group, the world leader in personnel recruitment. The company stands out for its commitment to inclusivity.

**Dataset Structure**

The company’s dataset, previously anonymized, contains multiple rows for each stored candidate. For each candidate, each row identifies a different step in the recruiting process. The columns can be divided into three macro-categories:

**CANDIDATE ATTRIBUTES:**

- **ID**: Unique identifier.
- **Candidate State**: Candidate status:

  - **Imported**: Candidates imported from external databases (e.g., AlmaLaurea). Some may never have responded to Akkodis. `Event_Type__Val = CV Request` indicates that the recruiter has not yet received the résumé.
  - **First contact**: Initial contacts (usually by phone). Some may have stopped communication or have an inadequate résumé (`Event_Feedback = Inadequate CV`).
  - **In selection**: Candidates in the selection phase, undergoing initial interviews for a job position.
  - **QM**: Candidates who have undergone a Qualification Meeting.
  - **Economic Proposal**: Candidates who have received an economic offer.
  - **Vivier**: Candidates with skills not aligned with the requirements but valid for future opportunities.
  - **Hired**: Candidate hired by the client company.

- **Age Range**: Candidate age range: \[< 20], \[20 – 25], \[26 – 30], \[31 – 35], \[36 – 40], \[40 – 45], \[> 45]
- **Residence**: Current residence.
- **Sex**: Candidate’s sex (Male | Female, default: Male).
- **Protected Category**: Indicates if the candidate belongs to protected categories (Art.1 and Art.18).
- **TAG**: Keywords used by the recruiter.
- **Study Area**: Academic field of study.
- **Study Title**: Academic qualification:

  - **Middle school diploma**
  - **Professional qualification**
  - **High school graduation**
  - **Three-year degree**
  - **Five-year degree**
  - **Master’s degree**
  - **Doctorate**

- **Years Experience**: Range of years of experience: \[0], \[0-1], \[1-3], \[3-5], \[5-7], \[7-10], \[+10]
- **Sector**: Sector of experience.
- **Last Role**: Last job or study role.
- **Year of Insertion**: Year of insertion into the database.
- **Year of Recruitment**: Year of hiring (only if `Candidate State = Hired`).
- **Current RAL**: Current salary.
- **Expected RAL**: Salary expectation.

**PROCESS ATTRIBUTES:**

These relate to a specific stage and change for the same candidate as they progress through the recruiting process.

- **Event\_Type\_\_Val**: Type of event/process stage:

  - **Initial**: Commercial note, CV Request, Contact note, Research Association.
  - **Central**: HR interview, BM interview, Technical interview, Qualification Meeting.
  - **Final**: Candidate notification, Sending SC to customer, Economic proposal, Notify candidate, Inadequate CV.

- **Event\_Feedback**: Feedback associated with the event (OK or KO, with possible comments).
- **Overall**: Interview score (only for central events).
- **Akkodis Headquarters**: Akkodis office handling the candidate.
- Scores assigned by the recruiter (1–4) during the interview:

  - **Technical Skills**
  - **Standing/Position**
  - **Communication**
  - **Dynamism**
  - **Mobility**
  - **English**

**JOB POSITION ATTRIBUTES:**

These fields are present only if the candidate was hired by the company in question.

- **Recruitment Request**: Company request.
- **Assumption Headquarters**: Office location of the position.
- **Job Family Hiring**: Job category.
- **Job Title Hiring**: Job title.
- **Job Description**: Role description.
- **Candidate Profile**: Ideal profile required.
- **Years Experience.1**: Required years of experience (range compatible with the candidate’s Years Experience).
- **Minimum RAL**: Minimum expected salary.
- **Maximum RAL**: Maximum expected salary.
- **Study Level**: Required education level (compatible with Study Title).
- **Study Area.1**: Required field of study (compatible with Study Area).
- **Linked\_search\_key**: Code `RSnn.nnnn` (nn = insertion year, nnnn = search number).

1. Data Cleaning
-----------------
We load the dataset, remove duplicates, unnecessary columns, undesired rows, and apply the remapping defined in the configuration file.

.. code-block:: python

    PATH = 'C:/Users/andre/Desktop/ProjectWork_AEQUITAS_AKKODIS/'
    df = (
        pd.read_excel(PATH + 'data/Dataset_2.0_Akkodis.xlsx')
            .rename(columns=lambda c: c.lstrip().title())
    )
    df = df.drop_duplicates(subset='Id', keep='last')
    df = df.drop(columns=config['drop_columns'])

    for col, remove_list in config['drop_rows'].items():
        df = df[~df[col].isin(remove_list)]

    for col, mapping in config['remap_rows'].items():
        df[col] = df[col].replace(mapping)

.. code-block:: python

    unuseful_columns = []
    for col in df.columns:
        null_count = df[col].isna().sum() / df.shape[0]
        if null_count > (float(config['drop_nan_columns_threshold']) / 100):
            unuseful_columns.append(col)
    df = df.drop(columns=unuseful_columns)

    for col, filler in config['fill_nan_columns'].items():
        if filler == '%MEAN%':
            media = round(df[col].mean())
            df[col].fillna(media, inplace=True)
        else:
            df[col].fillna(filler, inplace=True)

**Feature Mapping**

.. code-block:: python

    def gen_lists(df, specs):
        out = {}
        for name, p in specs.items():
            base = out.get(p['src'], df[p['src']].dropna().astype(str).unique())
            items = [
                x for x in base
                if not any(exc in x for exc in p.get('exc', []))
                   and (any(inc in x for inc in p.get('inc', [])) if 'inc' in p else True)
            ]
            for key in ('split', 'post'):
                if key in p:
                    sep, idx = p[key]
                    items = [x.split(sep)[idx] if sep in x else x for x in items]
            out[name] = sorted(set(items))
        return out

    def apply_field(val, p, lists, feature_cfg):
        if 'list' in p:
            return next((x for x in lists[p['list']] if x in str(val)), p['def'])
        if 'in' in p:
            return p['y'] if val in feature_cfg[p['in']] else p['n']
        if 'eq' in p:
            return p['y'] if str(val) == p['eq'] else p['n']

    for feature, feat_cfg in config['feature_remapping'].items():
        lists = gen_lists(df, feat_cfg['lists'])
        for col_name, col_cfg in feat_cfg['fields'].items():
            df[col_name] = df[col_cfg['src']].apply(lambda v, cfg=col_cfg: apply_field(v, cfg, lists, feat_cfg))
        df = df.drop(columns=feature, errors='ignore')

2. Data Loading & Understanding
-------------------------------
2.1 Feature Selection
~~~~~~~~~~~~~~~~~~~~~

**Target Selection**

The project’s objective is to develop AI models to be used in the preliminary stages of the recruiting process to analyze emerging biases. The choice of target was influenced by the dataset structure, which contains information on candidates and positions managed by Akkodis.
Based on available data, two possible automatic prediction targets were identified:

- **RAL**
    Predict the most appropriate salary for the candidate’s profile.
- **Status**
    Label the candidate-position pair as positive or negative, defining whether the candidate’s profile meets the company’s requirements.
    Specifically, a candidate is considered Positive if they meet one of the following situations:
    
    - Their Candidate State indicates they have been hired (Hired), received an economic offer (Economic proposal), or reached the Qualification Meeting (QM), a key evaluation phase.
    - Their latest Event_Feedback reports positive feedback, such as a live technical feedback (OK (live)), confirmation of imminent start of activity (OK (waiting for departure)), or explicit hiring confirmation (OK (hired)).
    - In any other case, the profile is labeled Negative, indicating it did not satisfy the company’s requirements at relevant decision-making levels.

The first hypothesis was discarded because over 90% of candidates do not have values for the RAL-related fields.
To distinguish between suitable and unsuitable candidates, it was necessary to define an explicit target variable; however, the original dataset does not contain a binary column for this purpose.
Therefore, the Status variable was created logically, based on the criteria just shown, from the Candidate State and Event_Feedback columns.
This choice is consistent with the goal of evaluating whether classification models respect fairness criteria in the hiring decision process.

.. code-block:: python

    mask = np.zeros(len(df), dtype=bool)
    for col, valid_values in config['status_positive_conditions'].items():
        mask |= df[col].isin(valid_values)
    df['Status'] = np.where(mask, 'Positive', 'Negative')

**Feature Statistics**

.. code-block:: python

    stats = pd.DataFrame(index=df.columns)
    stats['missing_values'] = df.isnull().sum()
    stats['min'] = df.min(numeric_only=True)
    stats['max'] = df.max(numeric_only=True)
    stats['mean'] = df.mean(numeric_only=True)
    stats['std'] = df.std(numeric_only=True)
    stats['1st_percentile'] = df.quantile(0.25, numeric_only=True)
    stats['2nd_percentile'] = df.quantile(0.50, numeric_only=True)
    stats['3rd_percentile'] = df.quantile(0.75, numeric_only=True)
    stats['type'] = df.dtypes
    stats['distinct_values'] = df.nunique()

.. code-block:: text

    | Column             | missing_values | min | max |     mean |      std | 1st_percentile | 2nd_percentile | 3rd_percentile |    type | distinct_values |
    | ------------------ | -------------: | --: | --: | -------: | -------: | -------------: | -------------: | -------------: | ------: | --------------: |
    | Candidate State    |              0 | NaN | NaN |      NaN |      NaN |            NaN |            NaN |            NaN |  object |               5 |
    | Age Range          |              0 | NaN | NaN |      NaN |      NaN |            NaN |            NaN |            NaN |  object |               7 |
    | Sex                |              0 | NaN | NaN |      NaN |      NaN |            NaN |            NaN |            NaN |  object |               2 |
    | Protected Category |              0 | NaN | NaN |      NaN |      NaN |            NaN |            NaN |            NaN |  object |               2 |
    | Study Area         |              0 | NaN | NaN |      NaN |      NaN |            NaN |            NaN |            NaN |  object |              10 |
    | Study Title        |              0 | NaN | NaN |      NaN |      NaN |            NaN |            NaN |            NaN |  object |               7 |
    | Years Experience   |              0 | NaN | NaN |      NaN |      NaN |            NaN |            NaN |            NaN |  object |               7 |
    | Sector             |            217 | NaN | NaN |      NaN |      NaN |            NaN |            NaN |            NaN |  object |              14 |
    | Job Family Hiring  |          2 137 | NaN | NaN |      NaN |      NaN |            NaN |            NaN |            NaN |  object |               7 |
    | Job Title Hiring   |          2 137 | NaN | NaN |      NaN |      NaN |            NaN |            NaN |            NaN |  object |              18 |
    | Event\_Feedback    |            932 | NaN | NaN |      NaN |      NaN |            NaN |            NaN |            NaN |  object |              15 |
    | Overall            |            964 | NaN | NaN |      NaN |      NaN |            NaN |            NaN |            NaN |  object |               8 |
    | Minimum Ral        |          2 373 | NaN | NaN |      NaN |      NaN |            NaN |            NaN |            NaN |  object |              15 |
    | Ral Maximum        |          2 310 | NaN | NaN |      NaN |      NaN |            NaN |            NaN |            NaN |  object |              17 |
    | Study Level        |          2 198 | NaN | NaN |      NaN |      NaN |            NaN |            NaN |            NaN |  object |               7 |
    | Current Ral        |          1 660 | NaN | NaN |      NaN |      NaN |            NaN |            NaN |            NaN |  object |              18 |
    | Expected Ral       |          1 668 | NaN | NaN |      NaN |      NaN |            NaN |            NaN |            NaN |  object |              18 |
    | Technical Skills   |            972 | 1.0 | 4.0 | 2.139130 | 0.648580 |            2.0 |            2.0 |            3.0 | float64 |               4 |
    | Comunication       |            972 | 1.0 | 4.0 | 2.274534 | 0.617064 |            2.0 |            2.0 |            3.0 | float64 |               4 |
    | Maturity           |            969 | 1.0 | 4.0 | 2.262244 | 0.600904 |            2.0 |            2.0 |            3.0 | float64 |               4 |
    | Dynamism           |            969 | 1.0 | 4.0 | 2.260384 | 0.602228 |            2.0 |            2.0 |            3.0 | float64 |               4 |
    | Mobility           |            968 | 1.0 | 4.0 | 2.163569 | 0.823108 |            2.0 |            2.0 |            3.0 | float64 |               4 |
    | English            |            972 | 1.0 | 4.0 | 2.759006 | 0.543047 |            3.0 |            3.0 |            3.0 | float64 |               4 |
    | Residence City     |              0 | NaN | NaN |      NaN |      NaN |            NaN |            NaN |            NaN |  object |             741 |
    | Residence Province |              0 | NaN | NaN |      NaN |      NaN |            NaN |            NaN |            NaN |  object |             112 |
    | Residence Region   |              0 | NaN | NaN |      NaN |      NaN |            NaN |            NaN |            NaN |  object |              21 |
    | Residence State    |              0 | NaN | NaN |      NaN |      NaN |            NaN |            NaN |            NaN |  object |              33 |
    | European Residence |              0 | NaN | NaN |      NaN |      NaN |            NaN |            NaN |            NaN |  object |               2 |
    | Italian Residence  |              0 | NaN | NaN |      NaN |      NaN |            NaN |            NaN |            NaN |  object |               2 |
    | Status             |              0 | NaN | NaN |      NaN |      NaN |            NaN |            NaN |            NaN |  object |               2 |

.. code-block:: python

    cols = 2
    n = len(config['visualize_columns'])
    rows = math.ceil(n / cols)

    fig, axes = plt.subplots(rows, cols, figsize=(cols*6, rows*4), constrained_layout=True)
    axes = axes.flatten()
    for i, lookup in enumerate(config['visualize_columns']):
        ax = axes[i]

        distrib = Counter(df[lookup])
        labels = config['categorical_columns_custom_orders'].get(lookup, list(distrib.keys()))
        counts = [distrib[label] for label in labels]
        distrib_df = pd.DataFrame({lookup: labels, 'Count': counts})

        distrib_df.plot(
            x=lookup,
            y='Count',
            kind='bar',
            legend=False,
            ax=ax
        )
        ax.set_title(lookup)
        ax.tick_params(axis='x', rotation=45)

    for j in range(i+1, len(axes)):
        axes[j].axis('off')

    plt.show()

.. image:: _static/count.png


**Sensitive Feature Selection**

In the context of algorithmic fairness analysis, sensitive variables were identified based on regulatory criteria (e.g., GDPR) and social relevance, with the aim of monitoring their impact on hiring rates and preventing potential discrimination. In particular, the following protected characteristics were studied:

- **Gender**  
    The dataset shows a marked underrepresentation of female candidates (20% of the total). However, the hiring rate for women is higher than for men: 8.3% versus 5.3%. This difference could reflect an organizational choice aimed at increasing gender diversity, or the higher qualification of female profiles.
- **Age Range**  
    More than 65% of candidates are under 30 years old, of which 17% are even under 20. However, hiring rates increase in more mature age ranges, peaking between 31 and 45 years, confirming a preference for professionals with more experience. Younger candidates (≤ 26 years) show overall lower hiring performance.
- **Italian Residence**  
    Candidates residing in Italy have a higher probability of being hired, likely due to logistical factors, regulatory constraints, and the presence of local offices.
    However, the number of non-residents in our sample is small, making it impossible to draw meaningful conclusions about their hiring rate. During the next data collection phase, it will therefore be essential to increase the representativeness of this group to analyze potential disparities.
- **Protected Category**  
    Those belonging to protected categories constitute only 0.6% of the sample (18 candidates), an incidence too low to allow reliable statistical evaluations of their selection outcome. To determine whether there are any substantive discrimination or differences, it is also essential in this case to increase the representativeness of the group in order to perform an adequate analysis of possible disparities.

The next step will consist of integrating these evaluations within the selection model development flow, applying fairness metrics and mitigation tools to ensure an equitable and transparent hiring process.

.. code-block:: python

    cols = 2
    n = len(config['sensitive_columns'])
    total_plots = n * 2
    rows = math.ceil(total_plots / cols)

    fig, axes = plt.subplots(rows, cols, figsize=(cols*6, rows*4), constrained_layout=True)
    axes = axes.flatten()
    for i, snstv_col in enumerate(config['sensitive_columns']):
        order = config['categorical_columns_custom_orders'].get(snstv_col, None)

        df_plot = df.copy()
        if order:
            df_plot[snstv_col] = pd.Categorical(
                df_plot[snstv_col],
                categories=order,
                ordered=True
            )

        ax_hist = axes[2 * i + 1]
        sns.histplot(
            data=df_plot,
            x=snstv_col,
            hue="Status",
            multiple="stack",
            palette="Set2",
            shrink=0.8,
            ax=ax_hist
        )
        ax_hist.set_title(f"Distribution of Status by {snstv_col}", fontsize=14)
        ax_hist.tick_params(axis='x', rotation=45)

        
        ax_bar = axes[2 * i]
        sns.barplot(
            data=df,
            x=snstv_col,
            y=(df['Status'] == 'Positive').astype(float),
            estimator=np.mean,
            order=order,
            hue=snstv_col,
            palette='Set2',
            ax=ax_bar
        )
        ax_bar.set_title(f"Positive Rate by {snstv_col}", fontsize=14)
        ax_bar.tick_params(axis='x', rotation=45)

    for j in range(2 * n, len(axes)):
        axes[j].axis('off')

    plt.show()

.. image:: _static/distribution.png


2.2 Proxy Identification
~~~~~~~~~~~~~~~~~~~~~~~~

**Cross-Correlation Analysis**

To highlight the relationships between the dataset’s columns and obtain a concise graphical representation, a correlation matrix was generated using Seaborn’s heatmap function.

.. code-block:: python

    columns_type = {}
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]):
            columns_type[col] = 'cat'
        elif pd.api.types.is_numeric_dtype(df[col]):
            columns_type[col] = 'num'

    encoding_mappings = {}
    df_corr = pd.DataFrame(index=df.index)
    for col, t in columns_type.items():
        if t == 'cat':
            if col in config['categorical_columns_custom_orders']:
                ordered = config['categorical_columns_custom_orders'][col]
                df_corr[col] = pd.Categorical(df[col], categories=ordered, ordered=True).codes
                encoding_mappings[col] = {cat: i for i, cat in enumerate(ordered)}
            else:
                encoder = LabelEncoder()
                df_corr[col] = encoder.fit_transform(df[col].astype(str))
                encoding_mappings[col] = dict(zip(encoder.classes_, encoder.transform(encoder.classes_)))
        else:
            df_corr[col] = df[col]

    plt.figure(figsize=(16, 10))
    sns.heatmap(df_corr.corr().round(2), annot=True, cmap='coolwarm', center=0, linewidths=.5)
    plt.title("Correlation Matrix")

.. image:: _static/corr1.png


.. code-block:: python

    df_num = df.select_dtypes(include='number')

    cat_cols = list(config['categorical_columns_custom_orders'].keys())

    df_cat_encoded = pd.DataFrame(
        { col: pd.Categorical(df[col],
                            categories=config['categorical_columns_custom_orders'][col],
                            ordered=True
                            ).codes
        for col in cat_cols },
        index=df.index
    )

    df_corr = pd.concat([df_num, df_cat_encoded], axis=1)

    plt.figure(figsize=(16, 10))
    sns.heatmap(df_corr.corr().round(2), annot=True, cmap='coolwarm', center=0, linewidths=.5)
    plt.title("Correlation Matrix of Numerical and Ordered Categorical Features")

.. image:: _static/corr2.png


.. code-block:: python

    corr_matrix = df_corr.corr().abs()

    # Create a mask to get the upper triangle (excluding the diagonal)
    upper_triangle_mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
    upper_triangle = corr_matrix.where(upper_triangle_mask)
    corr_pairs = upper_triangle.stack()

    high_corr_pairs = corr_pairs[corr_pairs > config['correlation_threshold']].sort_values(ascending=False)

    print("Variable pairs with correlation above the threshold:")
    print(high_corr_pairs)

.. code-block:: text

    Variable pairs with correlation above the threshold:
    Ral Maximum      Minimum Ral     0.839071
    Candidate State  Study Level     0.822850
    Current Ral      Expected Ral    0.818242
    Study Level      Ral Maximum     0.736592
    dtype: float64

**Chi-squared Test Analysis**

To identify the categorical variables that could be considered proxies for sensitive features, an analysis based on the chi-squared test was performed.

.. code-block:: python

    columns_type = {}
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]):
            columns_type[col] = 'cat'
        elif pd.api.types.is_numeric_dtype(df[col]):
            columns_type[col] = 'num'

    def compute(col1, col2):
        order = config['categorical_columns_custom_orders'].get(col1, None)
        contingency = pd.crosstab(df[col1], df[col2])
        if order:
            contingency = contingency.reindex(index=order)
        chi2, p, dof, expected = chi2_contingency(contingency, correction=False)
        test_name = 'Chi-squared'
        if contingency.shape == (2, 2) and (expected < 5).any():
            _, p = fisher_exact(contingency)
            test_name = "Fisher's exact"
        n = contingency.values.sum()
        k = min(contingency.shape)
        cramer_v = np.sqrt(chi2 / (n * (k - 1)))

        return contingency, expected, chi2, p, dof, cramer_v, test_name

    results = []
    cats = [col for col, t in columns_type.items() if t == 'cat']

    for col1, col2 in combinations(cats, 2):
        # Skip cause Residence attributes are highly correlated within themselves
        if 'Residence' in col1 or 'Residence' in col2:
            continue
        
        contingency, expected, chi2, p_raw, dof, cramer_v, test_name = compute(col1, col2)
        results.append({
            'col1':     col1,
            'col2':     col2,
            'chi2':     chi2,
            'p_raw':    p_raw,
            'dof':      dof,
            'cramer_v': cramer_v,
            'test':     test_name
        })
    res_df = pd.DataFrame(results)

    reject, p_bonf, _, _ = multipletests(res_df['p_raw'], method='bonferroni')
    res_df['p_bonf']      = p_bonf
    res_df['significant'] = reject

    thr_p = config['chi_squared_p_value_threshold']
    thr_v = config['cramers_v_threshold']
    mask = (res_df['p_bonf'] < thr_p) & (res_df['cramer_v'] >= thr_v)

    for _, row in res_df[mask].sort_values('cramer_v', ascending=False).iterrows():
        print(f"--- {row['col1']} vs {row['col2']} ---")
        print(f"{row['test']} test: "
            f"χ² = {row['chi2']:.2f}, "
            f"p (raw) = {row['p_raw']:.3e}, "
            f"p (Bonf.) = {row['p_bonf']:.3e}, "
            f"dof = {row['dof']}, "
            f"Cramér’s V = {row['cramer_v']:.3f}")
        print()

.. code-block:: text

    --- Age Range vs Years Experience ---
    Chi-squared test: χ² = 2092.78, p (raw) = 0.000e+00, p (Bonf.) = 0.000e+00, dof = 36, Cramér’s V = 0.368

    --- Study Area vs Study Title ---
    Chi-squared test: χ² = 1632.05, p (raw) = 5.224e-306, p (Bonf.) = 1.097e-304, dof = 54, Cramér’s V = 0.325

    --- Sex vs Study Area ---
    Chi-squared test: χ² = 214.75, p (raw) = 2.652e-41, p (Bonf.) = 5.570e-40, dof = 9, Cramér’s V = 0.288

2.3 Bias Detection
~~~~~~~~~~~~~~~~~~
To evaluate the level of Fairness of the trained models, three metrics were chosen:

* **Demographic Parity**
  This metric requires that each group have the same opportunity to be assigned to the positive class, regardless of true or false positives. An accurate model could turn out unfair if the subgroups in the test set are imbalanced with respect to the target variable Status.
* **Equalized Odds**
  This metric guarantees that the True Positive Rate (TPR) and False Positive Rate (FPR) remain constant across different groups. It means that the model should misclassify unqualified candidates as positive with equal probability for all categories, avoiding favoring or penalizing any particular subset.

.. code-block:: python

    cols = 2
    n = len(config['sensitive_columns'])
    rows = math.ceil(n / cols)

    fig, axes = plt.subplots(rows, cols, figsize=(cols*6, rows*4), constrained_layout=True)
    axes = axes.flatten()

    for i, sensitive_attr in enumerate(config['sensitive_columns']):
        y_true = (df["Status"] == 'Positive').astype(int)
        y_pred = y_true  # Measuring bias in the true labels
        s_attr = df[sensitive_attr]

        dpr = demographic_parity_ratio(y_true, y_pred, sensitive_features=s_attr)
        dpd = demographic_parity_difference(y_true, y_pred, sensitive_features=s_attr)

        mf = MetricFrame(
            metrics=selection_rate,
            y_true=y_true,
            y_pred=y_pred,
            sensitive_features=s_attr
        )
        sr_by_group = mf.by_group

        dir = sr_by_group.min() / sr_by_group.max()
        did = sr_by_group.max() - sr_by_group.min()

        metrics = [dpr, dpd, dir, did]
        labels = ['Statistical Parity Ratio',
                'Statistical Parity Difference',
                'Disparate Impact Ratio',
                'Disparate Impact Difference']
        
        ax = axes[i]
        ax.bar(labels, metrics)
        ax.set_title(sensitive_attr)
        ax.tick_params(axis='x', rotation=45)

    for j in range(i+1, len(axes)):
        axes[j].axis('off')

    plt.show()

.. image:: _static/pre_fairness.png


3. Training and Testing
-----------------------

**Dataset Categorical Attributes Sorting and Encoding**

.. code-block:: python

    columns_type = {}
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]):
            columns_type[col] = 'cat'
        elif pd.api.types.is_numeric_dtype(df[col]):
            columns_type[col] = 'num'

    encoding_mappings = {}
    df_corr = pd.DataFrame(index=df.index)
    for col, t in columns_type.items():
        if t == 'cat':
            if col in config['categorical_columns_custom_orders']:
                ordered = config['categorical_columns_custom_orders'][col]
                df_corr[col] = pd.Categorical(df[col], categories=ordered, ordered=True).codes
                encoding_mappings[col] = {cat: i for i, cat in enumerate(ordered)}
            else:
                encoder = LabelEncoder()
                df_corr[col] = encoder.fit_transform(df[col].astype(str))
                encoding_mappings[col] = dict(zip(encoder.classes_, encoder.transform(encoder.classes_)))
        else:
            df_corr[col] = df[col]

**Dataset Preparation**

.. code-block:: python

    n_splits = 2
    n_repeats = 3
    cv = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=random_seed)

    df = shuffle(df, random_state=random_seed)

    X_train = df.drop(columns=[target])
    y_train = df[target]
    s_train = df[sensitive]

    def to_aif360(X_df, y_df, s_df):
        df = X_df.copy()
        df[target] = y_df.values
        df[sensitive] = s_df.values
            
        return StandardDataset(
            df,
            label_name=target,
            favorable_classes=[1], # the value considered favorable (1)
            protected_attribute_names=sensitive,
            privileged_classes=[[1] for _ in sensitive] # values considered privileged
        )
    
**Models**

To ensure a comprehensive overview, models belonging to different algorithmic families were selected, including linear, probabilistic, tree-based, and neural network models.
The objective is to compare the results and relate performance to fairness. The selected models include:

* **Linear Models**

  * Linear Regression
  * Logistic Regression

* **Probabilistic Models**

  * Gaussian Naïve Bayes

* **Tree-based Models**

  * Decision Tree

* **Distance-based Models**

  * K-Nearest Neighbors

* **Neural Network**


3.1 No Mitigation - Baseline
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Models**

.. code-block:: python

    def create_model(seed, input_dim):
        tf.random.set_seed(seed)
        model = Sequential()
        model.add(Dense(128, input_dim=input_dim, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dense(128, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dense(128, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dense(64, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dense(1, activation='sigmoid'))

        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        return model

    models = {
        'Logistic Regression': LogisticRegression(),
        'Linear Regression': LinearRegression(),
        'Decision Tree': DecisionTreeClassifier(),
        'Naive Bayes': GaussianNB(),
        'XGBoost': XGBClassifier(),
        'KNN': KNeighborsClassifier(),
        'Neural Network': create_model(random_seed, X_train.shape[1]),
    }

**Training**

.. code-block:: python

    for fold, (tr_idx, va_idx) in enumerate(cv.split(X_train, y_train, s_train), start=1):
        X_tr, X_va = X_train.iloc[tr_idx], X_train.iloc[va_idx]
        y_tr, y_va = y_train.iloc[tr_idx], y_train.iloc[va_idx]
        s_tr, s_va = s_train.iloc[tr_idx], s_train.iloc[va_idx]

        for model_name, model in models.items():
            print(f"Training {model_name}...")
            if model_name == 'Neural Network':
                model.fit(X_tr, y_tr, epochs=20, batch_size=32, verbose=0)
                predictions[(fold, model_name)] = model.predict(X_va).ravel()
            else:
                model.fit(X_tr, y_tr)
                predictions[(fold, model_name)] = model.predict(X_va).ravel()

            predictions[(fold, model_name)] = (predictions[(fold, model_name)] > 0.5).astype(int)
            
            references[(fold, model_name)] = y_va.values
            sensitives[(fold, model_name)] = s_va.values

            print(f"{model_name} trained.")
            print(f"Predictions fold {fold} for {model_name}: {predictions[(fold, model_name)]}")


3.2 Pre-processing Mitigation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Pre-processing**

.. code-block:: python

    cr = CorrelationRemover(sensitive_feature_ids=sensitive, alpha=1)

    X_train_cr = pd.DataFrame(cr.fit_transform(X_train))

**Normalized Coordinate Plot - Original Vs Transformed Dataset**

.. code-block:: python

    X_orig_df = X_train_split.copy()
    X_orig_df.drop(columns=sensitive, inplace=True)
    X_trans_df = X_train_cr_df.copy()

    scaler = MinMaxScaler()
    X_orig_df_scaled = pd.DataFrame(
        scaler.fit_transform(X_orig_df),
        columns=X_orig_df.columns,
        index=X_orig_df.index
    )
    X_trans_df_scaled = pd.DataFrame(
        scaler.fit_transform(X_trans_df),
        columns=X_trans_df.columns,
        index=X_trans_df.index
    )

    X_trans_df_scaled.columns = X_orig_df_scaled.columns
    X_orig_df_scaled['version'] = 'Original'
    X_trans_df_scaled['version'] = 'Transformed'

    df_combined_scaled = pd.concat(
        [X_orig_df_scaled, X_trans_df_scaled],
        ignore_index=True
    )

    plt.figure(figsize=(16, 10))
    parallel_coordinates(
        df_combined_scaled,
        class_column='version',
        cols=list(X_orig_df.columns),
        color=['red', 'blue'],
        alpha=0.3,
        linewidth=0.7
    )

    plt.title("Parallel Coordinates (scaled) – Original vs Transformed")
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Scaled feature value [0–1]")
    plt.grid(axis='y', linestyle='--', linewidth=0.5)

.. image:: _static/plot_norm.png


**Coordinate Plot - Original Vs Transformed Dataset**

.. code-block:: python
    
    X_orig_df = X_train_split.copy()
    X_orig_df.drop(columns=sensitive, inplace=True)
    X_trans_df = X_train_cr_df.copy()

    X_trans_df.columns = X_orig_df.columns  # Ensure same columns for comparison
    X_orig_df['version'] = 'Original'
    X_trans_df['version'] = 'Transformed'

    df_combined = pd.concat([X_orig_df, X_trans_df], ignore_index=True)

    plt.figure(figsize=(16, 10))
    parallel_coordinates(
        df_combined,
        class_column='version',
        cols= df_combined.columns[:-1],  # Exclude 'version' column
        color=['red', 'blue'],      # Original→red, Transformed→blue
        alpha=0.3,                  # transparency to see overlap
        linewidth=0.7
    )

    plt.title("Parallel Coordinates – Original vs Transformed")
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Feature value")
    plt.grid(axis='y', linestyle='--', linewidth=0.5)  # light horizontal grid

.. image:: _static/plot.png


**Models**

.. code-block:: python

    def create_model(seed, input_dim):
        tf.random.set_seed(seed)
        model = Sequential()
        model.add(Dense(128, input_dim=input_dim, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dense(128, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dense(128, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dense(64, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dense(1, activation='sigmoid'))

        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        return model

    models = {
        'Logistic Regression': LogisticRegression(),
        'Linear Regression': LinearRegression(),
        'Decision Tree': DecisionTreeClassifier(),
        'Naive Bayes': GaussianNB(),
        'XGBoost': XGBClassifier(),
        'KNN': KNeighborsClassifier(),
        'Neural Network': create_model(random_seed, X_train_cr.shape[1]),
    }

**Training**

.. code-block:: python

    for fold, (train_idx, val_idx) in enumerate(cv.split(X_train_cr, y_train, s_train), start=1):
        X_tr, X_va = X_train_cr.iloc[train_idx], X_train_cr.iloc[val_idx]
        y_tr, y_va = y_train.iloc[train_idx], y_train.iloc[val_idx]
        s_tr, s_va = s_train.iloc[train_idx], s_train.iloc[val_idx]
        
        for model_name, model in models.items():
            print(f"Training {model_name}...")
            if model_name == 'Neural Network':
                model.fit(X_tr, y_tr, epochs=20, batch_size=32, verbose=0)
                predictions[(fold, f"{model_name}_preprocessed_cr")] = model.predict(X_va).ravel()
            else:
                model.fit(X_tr, y_tr)
                predictions[(fold, f"{model_name}_preprocessed_cr")] = model.predict(X_va).ravel()

            predictions[(fold, f"{model_name}_preprocessed_cr")] = (predictions[(fold, f"{model_name}_preprocessed_cr")] > 0.5).astype(int)
            
            references[(fold, f"{model_name}_preprocessed_cr")] = y_va.values
            sensitives[(fold, f"{model_name}_preprocessed_cr")] = s_va.values
            
            print(f"{model_name} trained.")
            temp = predictions[(fold, f"{model_name}_preprocessed_cr")]
            print(f"Preprocessed predictions for {model_name}: {temp}")    


3.3 In-processing Mitigation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Models**

.. code-block:: python

    models = {
        'Linear Regression': LinearRegression(),
    }

**In-processing and Training**

.. code-block:: python

    for fold, (tr_idx, va_idx) in enumerate(cv.split(X_train, y_train, s_train), start=1):
        X_tr, X_va = X_train.iloc[tr_idx], X_train.iloc[va_idx]
        y_tr, y_va = y_train.iloc[tr_idx], y_train.iloc[va_idx]
        s_tr, s_va = s_train.iloc[tr_idx], s_train.iloc[va_idx]

        train_ds = to_aif360(X_tr, y_tr, s_tr)
        val_ds = to_aif360(X_va, y_va, s_va)

        for model_name, model in models.items():
            gfc = GerryFairClassifier(
                C=10,
                gamma=0.01,
                fairness_def='FP',
                max_iters=10,
                printflag=False,
                heatmapflag=False,
                heatmap_iter=10,
                heatmap_path='.',
                predictor=model
            )
            gfc.fit(train_ds)
            pred_gfc = gfc.predict(val_ds)
            predictions[(fold, f"{model_name}_inprocessed_gfc")] = pred_gfc.labels.ravel()

            references[(fold, f"{model_name}_inprocessed_gfc")] = y_va.values
            sensitives[(fold, f"{model_name}_inprocessed_gfc")] = s_va.values
            
            temp = predictions[(fold, f"{model_name}_inprocessed_gfc")]
            print(f"Inprocessed predictions for {model_name}: {temp}")


3.4 Post-processing Mitigation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Models**

.. code-block:: python

    def create_model(seed, input_dim):
        tf.random.set_seed(seed)
        model = Sequential()
        model.add(Dense(128, input_dim=input_dim, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dense(128, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dense(128, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dense(64, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dense(1, activation='sigmoid'))

        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        return model

    models = {
        'Logistic Regression': LogisticRegression(),
        'Linear Regression': LinearRegression(),
        'Decision Tree': DecisionTreeClassifier(),
        'Naive Bayes': GaussianNB(),
        'XGBoost': XGBClassifier(),
        'KNN': KNeighborsClassifier(),
        'Neural Network': create_model(random_seed, X_train.shape[1]),
    }

**Training**

.. code-block:: python

    for fold, (tr_idx, va_idx) in enumerate(cv.split(X_train, y_train, s_train), start=1):
        X_tr, X_va = X_train.iloc[tr_idx], X_train.iloc[va_idx]
        y_tr, y_va = y_train.iloc[tr_idx], y_train.iloc[va_idx]
        s_tr, s_va = s_train.iloc[tr_idx], s_train.iloc[va_idx]

        for model_name, model in models.items():
            print(f"Training {model_name}...")
            if model_name == 'Neural Network':
                model.fit(X_tr, y_tr, epochs=10, batch_size=32, verbose=0)
                predictions[(fold, f"{model_name}_postprocessed_to")] = model.predict(X_va).ravel()
            else:
                model.fit(X_tr, y_tr)
                predictions[(fold, f"{model_name}_postprocessed_to")] = model.predict(X_va).ravel()

            print(f"{model_name} trained.")

        for model_name, model in models.items():
            to = ThresholdOptimizer(
                estimator=model,
                constraints='demographic_parity',
                objective='accuracy_score',
                prefit=True,
                grid_size=1000,
                flip=False,
                predict_method='predict'
            )
            to.fit(X_tr, y_tr, sensitive_features=s_tr)
            pred_to = to.predict(X_va, sensitive_features=s_va)
            predictions[(fold, f"{model_name}_postprocessed_to")] = pred_to.ravel()

            references[(fold, f"{model_name}_postprocessed_to")] = y_va.values
            sensitives[(fold, f"{model_name}_postprocessed_to")] = s_va.values
            
            temp = predictions[(fold, f"{model_name}_postprocessed_to")]
            print(f"Postprocessed predictions for {model_name}: {temp}")


4. Performance and Fairness Metrics Evaluation
----------------------------------------------

**Performance Metrics**

- Accuracy
- Precision
- Recall
- F1-score
- AUC

.. code-block:: python

    records = []
    for (fold, name), y_pred in predictions.items():

        y_test = references[fold, name]
        y_sens = sensitives[fold, name]

        scores = {
            'Fold':       fold,
            'Model':      name,
            'Accuracy':   accuracy_score(y_test, y_pred),
            'Precision':  precision_score(y_test, y_pred),
            'Recall':     recall_score(y_test, y_pred),
            'F1-score':   f1_score(y_test, y_pred),
            'ROC AUC':    roc_auc_score(y_test, y_pred),
            'Group':      'Processed' if any(tag in name for tag in ['preprocessed','inprocessed','postprocessed'])
                        else 'Base'
        }
        records.append(scores)

    df = pd.DataFrame(records).round(3)

    df = df.melt(
                    id_vars=['Fold','Model','Group'],
                    value_vars=['Accuracy','Precision','Recall','F1-score','ROC AUC'],
                    var_name='Metric',
                    value_name='Value'
                    )

    df = (
        df
        .groupby(['Model','Group','Metric'])['Value']
        .agg(['mean','std'])
        .reset_index()
    )

    base_models = df.loc[df.Group=='Base','Model'].unique()

    ncols = 3
    nrows = int(np.ceil(len(base_models)/ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols*4, nrows*3), sharey=True)
    axes = axes.flatten()

    pivot_mean = df.pivot(index='Metric', columns='Model', values='mean')
    pivot_std  = df.pivot(index='Metric', columns='Model', values='std')

    for ax, base in zip(axes, base_models):
        cols = [c for c in pivot_mean.columns if c.startswith(base)]
        x = np.arange(len(pivot_mean))
        width = 0.8 / len(cols)

        for i, var in enumerate(cols):
            label = var.replace(base + '_', '') if var != base else 'Base'
            ax.bar(
                x + (i - (len(cols)-1)/2)*width,
                pivot_mean[var],
                width,
                yerr=pivot_std[var],
                capsize=5,
                label=label
                )

        ax.set_xticks(x)
        ax.set_xticklabels(pivot_mean.index, rotation=45, ha='right')
        ax.set_title(base)
        ax.legend(fontsize='x-small')

    for ax in axes[len(base_models):]:
        ax.set_visible(False)

    plt.tight_layout()
    plt.show()

.. image:: _static/performance.png


**Fairness Metrics**

- Demographic Parity Ratio
- Equalized Odds Ratio
- Demographic Parity Difference
- Equalized Odds Difference

.. code-block:: python

    records = []
    for (fold, name), y_pred in predictions.items():
        y_test = references[fold, name]
        s_test = sensitives[fold, name]
        sf_df = pd.DataFrame(s_test.tolist(), columns=sensitive_features)

        mf = MetricFrame(
            metrics={
                'sel_rate': selection_rate,
                'fpr': false_positive_rate,
                'fnr': false_negative_rate,
                'count': count
            },
            y_true=y_test,
            y_pred=y_pred,
            sensitive_features=sf_df
        )
        dp_diff   = demographic_parity_difference(y_test, y_pred, sensitive_features=sf_df)
        eo_diff   = equalized_odds_difference(y_test, y_pred, sensitive_features=sf_df)
        dp_ratio  = demographic_parity_ratio(y_test, y_pred, sensitive_features=sf_df)
        eo_ratio  = equalized_odds_ratio(y_test, y_pred, sensitive_features=sf_df)

        for group_val, metrics in mf.by_group.iterrows():
            for metric in ['sel_rate', 'fpr', 'fnr', 'count']:
                records.append({
                    'Model':  name,
                    'Group':  group_val,
                    'Metric': metric,
                    'Value':  metrics[metric]
                })

        records.append({'Model': name, 'Group': 'OverallDiff',  'Metric': 'dp_diff',   'Value': dp_diff})
        records.append({'Model': name, 'Group': 'OverallDiff',  'Metric': 'eo_diff',   'Value': eo_diff})
        records.append({'Model': name, 'Group': 'OverallRatio', 'Metric': 'dp_ratio',  'Value': dp_ratio})
        records.append({'Model': name, 'Group': 'OverallRatio', 'Metric': 'eo_ratio',  'Value': eo_ratio})

    df = pd.DataFrame(records).round(3)

    df = (
        df
        .groupby(['Model','Group','Metric'])['Value']
        .agg(['mean','std'])
        .reset_index()
    )

    base_models = [
        m for m in df['Model'].unique()
        if not any(tag in m for tag in ('preprocessed','inprocessed','postprocessed'))
    ]

    ncols = 3
    nrows = int(np.ceil(len(base_models) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols * 5, nrows * 4), sharey=True)
    axes = axes.flatten()

    global_diff = df[
        (df['Group'] == 'OverallDiff') &
        (df['Metric'].isin(['dp_diff','eo_diff']))
    ]

    global_ratio = df[
        (df['Group'] == 'OverallRatio') &
        (df['Metric'].isin(['dp_ratio','eo_ratio']))
    ]

    group_metrics = df[
        (df['Metric'].isin(['fnr','fpr','sel_rate'])) &
        (~df['Group'].isin(['OverallDiff','OverallRatio']))
    ]

    group_agg = (
        group_metrics
        .groupby(['Model','Metric'])[['mean','std']]
        .mean()
        .reset_index()
    )

    flat = pd.concat([global_diff, global_ratio, group_agg], ignore_index=True)

    pivot_mean = flat.pivot(index='Metric', columns='Model', values='mean')
    pivot_std  = flat.pivot(index='Metric', columns='Model', values='std')
        
    for ax, base in zip(axes, base_models):
        cols = [c for c in pivot_mean.columns if c.startswith(base)]
        x = np.arange(len(pivot_mean))
        width = 0.8 / len(cols)

        for i, var in enumerate(cols):
            label = var.replace(base + '_', '') if var != base else 'Base'
            ax.bar(
                x + (i - (len(cols)-1)/2)*width,
                pivot_mean[var],
                width,
                yerr=pivot_std[var],
                capsize=5,
                label=label
            )

        ax.set_xticks(x)
        ax.set_xticklabels(pivot_mean.index, rotation=45, ha='right')
        ax.set_title(base)
        ax.legend(fontsize='x-small')

    for ax in axes[len(base_models):]:
        ax.set_visible(False)

    plt.tight_layout()
    plt.show()

.. image:: _static/fairness.png


**Final Commentary on Fairness Results**

The comparative analysis of the three mitigation strategies (pre-processing with CorrelationRemover, in-processing with GerryFairClassifier and post-processing with ThresholdOptimizer) applied to the seven models clearly highlights the following points:

1. **Pre-processing (CorrelationRemover)**

   * Ensures a better compromise: it consistently improves the **Demographic Parity difference** and the **Equalized Odds Difference** without overly drastic impacts on *False Negative Rate*/*False Positive Rate*, thus maintaining classification performance similar to the baseline model.

2. **In-processing (GerryFairClassifier)**

   * Applied here only to Linear Regression, it offers intermediate benefits between pre-processing and post-processing: it reduces the **Demographic Parity difference** quite well but is less effective on the **Equalized Odds Difference**, and the method’s complexity overhead is higher.

3. **Post-processing (ThresholdOptimizer)**

   * It is the most effective lever for reducing both the **Demographic Parity difference** and the **Equalized Odds Difference**, bringing their values close to zero in almost all models.
   * However, this “flattening effect” is achieved at the cost of a slight worsening in absolute error rates (*False Negative Rate*/*False Positive Rate*) and some variation in the overall selection rate.

4. **Model Robustness**

   * **XGBoost** and **Naïve Bayes** start from lower disparity values and undergo smaller adjustments, making them the most “intrinsically fair” on the tested data.
   * **Decision Tree** and **KNN** show the greatest fairness gains (and, correspondingly, the greatest trade-offs in error rates).
   
   Both of these findings confirm that the choice of model significantly influences the effectiveness of each mitigation strategy.

5. **Operational Choice**

   * If the primary objective is to **maximize fairness**, post-processing should be the first choice.
   * If instead you desire a more delicate **balance between fairness and accuracy**, pre-processing allows you to “smooth out” biases without excessively compromising performance.

In conclusion, integrating these insights into the model production workflow enables the selection of the mitigation strategy best suited to business objectives, balancing fairness, transparency, and predictive performance.

.. raw:: html

   <div style="overflow-x:auto;">

.. raw:: html

   <div style="width:1500px;">

.. list-table:: Fairness Strategies Analysis
   :header-rows: 1
   :widths: 1 1 1 1 1 1 1 1

   * - Technique / Model
     - Decision Tree
     - KNN
     - Linear Regression
     - Logistic Regression
     - Naive Bayes
     - Neural Network
     - XGBoost
   * - Pre-processing
     - Improves **Demographic Parity** and **Equalized Odds**; *FNR* increases and *FPR* increases.
     - **Demographic Parity** mixed; **Equalized Odds** mixed; *FNR* increases and *FPR* increases.
     - **Demographic Parity** improves; **Equalized Odds** mixed; *FNR* decreases and *FPR* decreases.
     - **Demographic Parity** mixed; **Equalized Odds** improves; *FNR* increases and *FPR* increases.
     - **Demographic Parity** mixed; **Equalized Odds** mixed; *FNR* decreases and *FPR* increases significantly.
     - **Demographic Parity** worsens; **Equalized Odds** worsens; *FNR* increases and *FPR* increases.
     - **Demographic Parity** worsens; **Equalized Odds** mixed; *FNR* decreases and *FPR* decreases.
   * - In-processing
     - —
     - —
     - Offers no clear improvement in **Demographic Parity** or **Equalized Odds**; *FNR* and *FPR* stable.
     - —
     - —
     - —
     - —
   * - Post-processing
     - Improves **Demographic Parity** and **Equalized Odds**; *FNR* increases and *FPR* decreases.
     - **Demographic Parity** mixed; **Equalized Odds** mixed; *FNR* decreases and *FPR* increases.
     - **Demographic Parity** improves; **Equalized Odds** improves; *FNR* decreases and *FPR* decreases.
     - **Demographic Parity** improves; **Equalized Odds** improves; *FNR* increases and *FPR* increases.
     - **Demographic Parity** mixed; **Equalized Odds** mixed; *FNR* increases and *FPR* increases.
     - **Demographic Parity** worsens; **Equalized Odds** worsens; *FNR* increases and *FPR* increases.
     - Improves **Demographic Parity**; **Equalized Odds** stable; *FNR* increases and *FPR* decreases.

.. raw:: html

   </div>

.. raw:: html

   </div>
   