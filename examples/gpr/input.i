[StochasticTools]
[]

[Distributions]
  [T_dist]
    type = Uniform
    lower_bound = 300
    upper_bound = 1500
  []
[]

[Samplers]
  [train_sample]
    type = MonteCarlo
    num_rows = 6
    distributions = 'T_dist'
    execute_on = PRE_MULTIAPP_SETUP
  []
[]

[MultiApps]
  [sub]
    type = SamplerFullSolveMultiApp
    input_files = MoRu.i
    sampler = train_sample
    reset_apps = 0
    reset_time = 1
  []
[]

[Controls]
  [cmdline]
    type = MultiAppSamplerControl
    multi_app = sub
    sampler = train_sample
    param_names = 'ChemicalComposition/temperature'
  []
[]

[Transfers]
  [data]
    type = SamplerReporterTransfer
    from_multi_app = sub
    sampler = train_sample
    stochastic_reporter = results
    from_reporter = 'avg/value'
  []
[]

[Reporters]
  [results]
    type = StochasticReporter
  []
  [train_avg]
    type = EvaluateSurrogate
    model = gauss_process_avg
    sampler = train_sample
    evaluate_std = 'true'
    parallel_type = ROOT
    execute_on = final
  []
[]

[Trainers]
  [GP_avg_trainer]
    type = GaussianProcessTrainer
    execute_on = timestep_end
    sampler = train_sample
    response = results/data:avg:value
    covariance_function = 'rbf'
    standardize_params = 'true' #Center and scale the training params
    standardize_data = 'true' #Center and scale the training data
  []
[]

[Covariance]
  [rbf]
    type = SquaredExponentialCovariance
    signal_variance = 1 #Use a signal variance of 1 in the kernel
    noise_variance = 1e-3 #A small amount of noise can help with numerical stability
    length_factor = '0.5' #Select a length factor for each parameter (k and q)
  []
[]

[Surrogates]
  [gauss_process_avg]
    type = GaussianProcess
    trainer = 'GP_avg_trainer'
  []
[]

[Outputs]
  csv = true
  execute_on = FINAL
[]

