import 'package:flutter/material.dart';
import '../../core/components/custom_button.dart';
import '../../core/components/input_field.dart';
import '../../core/theme/app_colors.dart';

class SignUpScreen extends StatelessWidget {
  const SignUpScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'Join Jakairta',
                style: Theme.of(context).textTheme.displayLarge?.copyWith(
                  fontSize: 32,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Create an account to stay safe from floods.',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 32),
              const InputField(
                hintText: 'Full Name',
                prefixIcon: Icons.person_outline,
              ),
              const SizedBox(height: 16),
              const InputField(
                hintText: 'Email',
                prefixIcon: Icons.email_outlined,
              ),
              const SizedBox(height: 16),
              const InputField(
                hintText: 'Phone Number',
                prefixIcon: Icons.phone_outlined,
              ),
              const SizedBox(height: 16),
              const InputField(
                hintText: 'Password',
                prefixIcon: Icons.lock_outline,
                obscureText: true,
              ),
              const SizedBox(height: 32),
              CustomButton(
                text: 'Sign Up',
                onPressed: () {
                  // Navigate back to login
                  Navigator.of(context).pop();
                },
              ),
              const SizedBox(height: 24),
              Text(
                'By signing up, you agree to our Terms & Privacy Policy.',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontSize: 12,
                ),
              ),
              const SizedBox(height: 48),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  _buildFeatureIcon(Icons.warning_amber_rounded, 'Alerts', context),
                  _buildFeatureIcon(Icons.videocam_outlined, 'CCTV', context),
                  _buildFeatureIcon(Icons.security, 'Safe Zones', context),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFeatureIcon(IconData icon, String label, BuildContext context) {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: AppColors.primary.withOpacity(0.1),
            shape: BoxShape.circle,
          ),
          child: Icon(icon, color: AppColors.primary),
        ),
        const SizedBox(height: 8),
        Text(
          label,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            fontSize: 12,
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }
}
