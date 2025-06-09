Fairness Pipeline Documentation
===============================

1. Data Cleaning
----------------

Carichiamo il dataset, rimuoviamo i duplicati, colonne inutili, righe non desiderate, e applichiamo il remapping definito nel file di configurazione.

**Lettura e pulizia iniziale del dataset**

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

**Rimozione colonne con troppi valori nulli e riempimento con valori di default**

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

**Remapping della feature Residence tramite liste configurabili**

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

**Creazione colonna "Status" binaria**

.. code-block:: python

    mask = np.zeros(len(df), dtype=bool)
    for col, valid_values in config['status_positive_conditions'].items():
        mask |= df[col].isin(valid_values)
    df['Status'] = np.where(mask, 'Positive', 'Negative')


2. Data Loading & Understanding
-------------------------------
2.1 Feature Selection
~~~~~~~~~~~~~~~~~~~~~

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

    for lookup in config['visualize_columns']:
        distrib = Counter(df[lookup])
        labels = config['categorical_columns_custom_orders'].get(lookup, distrib.keys())
        counts = [distrib[label] for label in labels]
        distrib_df = pd.DataFrame({lookup: labels, 'Count': counts})
        plt.figure(figsize=(8, 5))
        distrib_df.head(20).plot(x=lookup, y='Count', kind='bar', legend=False)
        plt.title(lookup)

.. code-block:: python

    for snstv_col in config['sensitive_columns']:
        order = config['categorical_columns_custom_orders'].get(snstv_col)

        plt.figure(figsize=(8, 5))
        sns.barplot(
            data=df,
            x=snstv_col,
            y=(df['Status'] == 'Positive').astype(float),
            estimator=np.mean,
            order=order,
            hue=snstv_col,
            palette='Set2'
        )
        plt.title(f"Status Positive Rate by {snstv_col}", fontsize=14)
        plt.xticks(rotation=45)

        df_plot = df.copy()
        if order:
            df_plot[snstv_col] = pd.Categorical(df_plot[snstv_col], categories=order, ordered=True)
        
        plt.figure(figsize=(8, 5))
        sns.histplot(
            data=df_plot,
            x=snstv_col,
            hue="Status",
            multiple="stack",
            palette="Set2",
            shrink=0.8
        )
        plt.title(f"Distribution of Status by {snstv_col}", fontsize=14)
        plt.xticks(rotation=45)

**Identificazione delle Feature Sensibili**
Nel contesto dell’equità algoritmica, è fondamentale identificare correttamente le feature sensibili, ovvero quelle variabili che rappresentano caratteristiche protette degli individui e che, se utilizzate impropriamente, possono introdurre o amplificare bias discriminatori.
In questo progetto, le feature sensibili sono state individuate sulla base di criteri normativi (es. GDPR) e rilevanza sociale.
Sono state considerate sensibili le variabili che descrivono aspetti come il genere, la cittadinanza, la residenza e altre caratteristiche personali potenzialmente soggette a disparità di trattamento.
La selezione è stata effettuata analizzando le distribuzioni di tali feature e verificandone l’impatto sui tassi di assunzione.

    - **1. Gender (Sex)**
    Females are hired at a significantly higher rate than males, suggesting a possible organizational emphasis on gender diversity or a potential bias favoring female candidates.

    - **2. Age Range**
    Hiring rates increase with age, peaking between 31–45 years, indicating a clear preference for mid-career professionals with more experience. Younger candidates, especially under 26, face notably lower hiring chances.

    - **3. European Residence**
    Candidates residing in Europe are far more likely to be hired, which may reflect logistical preferences, legal work eligibility, or alignment with company locations and operations.

    - **4. Italian Residence**
    There is a strong hiring bias toward candidates living in Italy. This suggests the organization prefers local hires, potentially to reduce relocation costs or due to legal/employment constraints.

    - **5. Protected Category**
    No meaningful difference in hiring rates between protected and non-protected groups was found. However, due to the very small sample of protected category candidates, no reliable conclusion can be drawn.

**Definizione della Feature Target**
La feature target è la variabile che il modello ha il compito di predire.
In questo caso, essa rappresenta l'esito di un processo decisionale, ovvero lo stato di assunzione del candidato.
Tuttavia, il dataset originale non contiene una colonna esplicita binaria per questo scopo.
Pertanto, è stata costruita una variabile target denominata Status, derivata da una combinazione logica di due colonne esistenti: Candidate State ed Event_Feedback.
Questa scelta è coerente con l’obiettivo del progetto, che è valutare se il modello di classificazione rispetti criteri di equità nel processo decisionale relativo all’assunzione dei candidati.

2.2 Proxy Identification
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    columns_type = {}
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]):
            columns_type[col] = 'cat'
        elif pd.api.types.is_numeric_dtype(df[col]):
            columns_type[col] = 'num'

.. code-block:: python

    num_cols = [col for col, t in columns_type.items() if t == 'num']
    df_num = df[num_cols].copy()

    ordered_categorical_columns = [
        col for col in df.columns if col in config['categorical_columns_custom_orders']
    ]

    df_cat = df[ordered_categorical_columns].copy()

    for col in ordered_categorical_columns:
        order = config['categorical_columns_custom_orders'][col]
        df_cat[col] = pd.Categorical(df_cat[col], categories=order, ordered=True)

    df_cat_encoded = df_cat.apply(lambda x: x.cat.codes)

    df_corr = pd.concat([df_num, df_cat_encoded], axis=1)

    plt.figure(figsize=(16, 10))
    sns.heatmap(df_corr.corr().round(2), annot=True, cmap='coolwarm', center=0, linewidths=.5)
    plt.title("Correlation Matrix of Numerical and Ordered Categorical Features")

.. code-block:: python

    corr_matrix = df_corr.corr().abs()

    # Create a mask to get the upper triangle (excluding the diagonal)
    upper_triangle_mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
    upper_triangle = corr_matrix.where(upper_triangle_mask)
    corr_pairs = upper_triangle.stack()

    high_corr_pairs = corr_pairs[corr_pairs > config['correlation_threshold']].sort_values(ascending=False)

    print("Variable pairs with correlation above the threshold:")
    print(high_corr_pairs)

.. code-block:: python

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

    cats = [col for col, t in columns_type.items() if t == 'cat']
    for col1, col2 in combinations(cats, 2):
        if col1 == col2:
            continue
         
        contingency, expected, chi2, p, dof, cramer_v, test_name = compute(col1, col2)

        if p < config['chi_squared_p_value_threshold'] and cramer_v >= config['cramers_v_threshold']:
            print(f"--- {col1} vs {col2} ---")
            #print("Actual frequencies:")
            #print(contingency)
            #print()
            #print("Expected frequencies:")
            #print(pd.DataFrame(expected, index=contingency.index, columns=contingency.columns))
            #print()
            print(f"{test_name} test: χ² = {chi2:.2f}, p = {p:.3f}, dof = {dof}, Cramér’s V = {cramer_v:.3f}")
            print()

2.3 Bias Detection
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def compute_bias_metrics(df, sensitive_column, target_column):
        y_true = (df[target_column] == 'Positive').astype(int)
        y_pred = y_true  # Measuring bias in the true labels
        s_attr = df[sensitive_column]

        dpd = demographic_parity_difference(y_true, y_pred, sensitive_features=s_attr)

        mf = MetricFrame(metrics=selection_rate, y_true=y_true, y_pred=y_pred, sensitive_features=s_attr)
        sr_by_group = mf.by_group
        di = sr_by_group.min() / sr_by_group.max()

        print(f"\n=== Bias metrics for: {sensitive_column} ===")
        print(f"Statistical Parity Difference: {dpd:.4f}")
        print(f"Disparate Impact (min/max rate): {di:.4f}")
        print("\nSelection Rates by group:")
        print(sr_by_group)

    for sensitive_attr in config['sensitive_columns']:
        compute_bias_metrics(df, sensitive_attr, 'Status')

3. Training and Testing
-----------------------

.. code-block:: python

    columns_type = {}
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]):
            columns_type[col] = 'cat'
        elif pd.api.types.is_numeric_dtype(df[col]):
            columns_type[col] = 'num'

    encoding_mappings = {}
    for col in [col for col, t in columns_type.items() if t == 'cat']:
        if col in config['categorical_columns_custom_orders']:
            df[col] = pd.Categorical(df[col], categories=config['categorical_columns_custom_orders'][col], ordered=True).codes
            encoding_mappings[col] = {cat: i for i, cat in enumerate(config['categorical_columns_custom_orders'][col])}
        else:
            encoder = LabelEncoder()
            df[col] = encoder.fit_transform(df[col].astype(str))
            encoding_mappings[col] = dict(zip(encoder.classes_, encoder.transform(encoder.classes_)))

3.1 Pre-processing Mitigation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    cr = CorrelationRemover(sensitive_feature_ids=sensitive, alpha=1)

    X_train_cr = cr.fit_transform(train_df)
    X_train_cr_df = pd.DataFrame(X_train_cr)

    X_test_cr = cr.transform(test_df)
    X_test_cr_df = pd.DataFrame(X_test_cr)

- **Coordinate Plot - Original Vs Transformed Dataset**

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
        'Neural Network': create_model(random_seed, X_train_cr_df.shape[1]),
    }

.. code-block:: python

    for model_name, model in models.items():
        print(f"Training {model_name}...")
        if model_name == 'Neural Network':
            model.fit(X_train_cr_df, y_train_split, epochs=10, batch_size=32, verbose=0)
            predictions[f"{model_name}_preprocessed_cr"] = model.predict(X_test_cr_df).flatten()
        else:
            model.fit(X_train_cr_df, y_train_split)
            predictions[f"{model_name}_preprocessed_cr"] = model.predict(X_test_cr_df)

        if model_name in ['Linear Regression', 'XGBoost', 'Neural Network']:
            predictions[f"{model_name}_preprocessed_cr"] = (predictions[f"{model_name}_preprocessed_cr"] > 0.5).astype(int)
        
        print(f"{model_name} trained.")
        temp = predictions[f"{model_name}_preprocessed_cr"]
        print(f"Preprocessed predictions for {model_name}: {temp}")
    
- **Performance bar-plot**
  - Accuracy
  - Precision
  - Recall
  - F1-score
  - AUC

.. code-block:: python

    metrics = []
    for name in predictions_df.columns:
        y_pred = predictions_df[name]
        accuracy = round(accuracy_score(y_test, y_pred), 3)
        precision = round(precision_score(y_test, y_pred), 3)
        recall = round(recall_score(y_test, y_pred), 3)
        f1 = round(f1_score(y_test, y_pred), 3)
        roc_auc = round(roc_auc_score(y_test, y_pred), 3)

        metrics.append({
            'Model': name,
            'Accuracy': accuracy,
            'Precision': precision,
            'Recall': recall,
            'F1-score': f1,
            'ROC AUC': roc_auc
        })
    metrics = pd.DataFrame(metrics)


- **Fairness bar-plot**
  - Demographic Parity Ratio
  - Equalized Odds Ratio

.. code-block:: python
    
    def compute_fairness_metrics(y_true, y_pred, s_test, label=None):
        mf = MetricFrame(
            metrics={
                'selection_rate': selection_rate,
                'fpr': false_positive_rate,
                'fnr': false_negative_rate,
                'count': count
            },
            y_true=y_true,
            y_pred=y_pred,
            sensitive_features=s_test
        )

        dp_diff = demographic_parity_difference(y_true, y_pred, sensitive_features=s_test)
        eo_diff = equalized_odds_difference(y_true, y_pred, sensitive_features=s_test)

        dp = demographic_parity_ratio(y_true, y_pred, sensitive_features=s_test)
        eo = equalized_odds_ratio(y_true, y_pred, sensitive_features=s_test)

        if label:
            print(f"=== {label} ===")

        print("By group:")
        print(mf.by_group)
        print()
        print("Overall (selection_rate, fpr, fnr, count):")
        print(mf.overall)
        print()
        print(f"Demographic parity difference: {dp_diff:.4f}")
        print(f"Equalized odds difference:     {eo_diff:.4f}\n")
        print()
        print(f"Demographic parity ratio: {dp:.4f}")
        print(f"Equalized odds ratio:     {eo:.4f}\n")

        return mf

    for name in predictions_df.columns:
        compute_fairness_metrics(y_test, predictions_df[name], s_test, label=name)

3.2 In-processing Mitigation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    models = {
        'Linear Regression': LinearRegression(),
    }

.. code-block:: python

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
        pred_gfc = gfc.predict(test_ds)
        predictions[f"{model_name}_inprocessed_gfc"] = pred_gfc.labels.ravel()
        temp = predictions[f"{model_name}_inprocessed_gfc"]
        print(f"Inprocessed predictions for {model_name}: {temp}")

- **Performance bar-plot**
  - Accuracy
  - Precision
  - Recall
  - F1-score
  - AUC

.. code-block:: python

    metrics = []
    for name in predictions_df.columns:
        y_pred = predictions_df[name]
        accuracy = round(accuracy_score(y_test, y_pred), 3)
        precision = round(precision_score(y_test, y_pred), 3)
        recall = round(recall_score(y_test, y_pred), 3)
        f1 = round(f1_score(y_test, y_pred), 3)
        roc_auc = round(roc_auc_score(y_test, y_pred), 3)

        metrics.append({
            'Model': name,
            'Accuracy': accuracy,
            'Precision': precision,
            'Recall': recall,
            'F1-score': f1,
            'ROC AUC': roc_auc
        })
    metrics = pd.DataFrame(metrics)


- **Fairness bar-plot**
  - Demographic Parity Ratio
  - Equalized Odds Ratio

.. code-block:: python

    def compute_fairness_metrics(y_true, y_pred, s_test, label=None):
        mf = MetricFrame(
            metrics={
                'selection_rate': selection_rate,
                'fpr': false_positive_rate,
                'fnr': false_negative_rate,
                'count': count
            },
            y_true=y_true,
            y_pred=y_pred,
            sensitive_features=s_test
        )

        dp_diff = demographic_parity_difference(y_true, y_pred, sensitive_features=s_test)
        eo_diff = equalized_odds_difference(y_true, y_pred, sensitive_features=s_test)

        dp = demographic_parity_ratio(y_true, y_pred, sensitive_features=s_test)
        eo = equalized_odds_ratio(y_true, y_pred, sensitive_features=s_test)

        if label:
            print(f"=== {label} ===")

        print("By group:")
        print(mf.by_group)
        print()
        print("Overall (selection_rate, fpr, fnr, count):")
        print(mf.overall)
        print()
        print(f"Demographic parity difference: {dp_diff:.4f}")
        print(f"Equalized odds difference:     {eo_diff:.4f}\n")
        print()
        print(f"Demographic parity ratio: {dp:.4f}")
        print(f"Equalized odds ratio:     {eo:.4f}\n")

        return mf

    for name in predictions_df.columns:
        compute_fairness_metrics(y_test, predictions_df[name], s_test, label=name)

3.3 Post-processing Mitigation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
        'Neural Network': create_model(random_seed, train_df.shape[1]),
    }

.. code-block:: python

    for model_name, model in models.items():
        print(f"Training {model_name}...")
        if model_name == 'Neural Network':
            model.fit(train_df, y_train_split, epochs=10, batch_size=32, verbose=0)
            predictions[f"{model_name}_postprocessed_to"] = model.predict(test_df).flatten()
        else:
            model.fit(train_df, y_train_split)
            predictions[f"{model_name}_postprocessed_to"] = model.predict(test_df)

        print(f"{model_name} trained.")

.. code-block:: python

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
        to.fit(train_df, y_train_split, sensitive_features=s_train_split)
        pred_to = to.predict(test_df, sensitive_features=s_test_split)
        predictions[f"{model_name}_postprocessed_to"] = pred_to.ravel()
        temp = predictions[f"{model_name}_postprocessed_to"]
        print(f"Postprocessed predictions for {model_name}: {temp}")

- **Performance bar-plot**
  - Accuracy
  - Precision
  - Recall
  - F1-score
  - AUC

.. code-block:: python

    metrics = []
    for name in predictions_df.columns:
        y_pred = predictions_df[name]
        accuracy = round(accuracy_score(y_test, y_pred), 3)
        precision = round(precision_score(y_test, y_pred), 3)
        recall = round(recall_score(y_test, y_pred), 3)
        f1 = round(f1_score(y_test, y_pred), 3)
        roc_auc = round(roc_auc_score(y_test, y_pred), 3)

        metrics.append({
            'Model': name,
            'Accuracy': accuracy,
            'Precision': precision,
            'Recall': recall,
            'F1-score': f1,
            'ROC AUC': roc_auc
        })
    metrics = pd.DataFrame(metrics)


- **Fairness bar-plot**
  - Demographic Parity Ratio
  - Equalized Odds Ratio

.. code-block:: python

    def compute_fairness_metrics(y_true, y_pred, s_test, label=None):
        mf = MetricFrame(
            metrics={
                'selection_rate': selection_rate,
                'fpr': false_positive_rate,
                'fnr': false_negative_rate,
                'count': count
            },
            y_true=y_true,
            y_pred=y_pred,
            sensitive_features=s_test
        )

        dp_diff = demographic_parity_difference(y_true, y_pred, sensitive_features=s_test)
        eo_diff = equalized_odds_difference(y_true, y_pred, sensitive_features=s_test)

        dp = demographic_parity_ratio(y_true, y_pred, sensitive_features=s_test)
        eo = equalized_odds_ratio(y_true, y_pred, sensitive_features=s_test)

        if label:
            print(f"=== {label} ===")

        print("By group:")
        print(mf.by_group)
        print()
        print("Overall (selection_rate, fpr, fnr, count):")
        print(mf.overall)
        print()
        print(f"Demographic parity difference: {dp_diff:.4f}")
        print(f"Equalized odds difference:     {eo_diff:.4f}\n")
        print()
        print(f"Demographic parity ratio: {dp:.4f}")
        print(f"Equalized odds ratio:     {eo:.4f}\n")

        return mf

    for name in predictions_df.columns:
        compute_fairness_metrics(y_test, predictions_df[name], s_test, label=name)
