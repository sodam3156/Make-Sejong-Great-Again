using System;
using UnityEngine;
using UnityEngine.UIElements;

namespace Tats.Game.UI.Settings
{
    /// <summary>
    /// SettingsScreen.uxml에 바인딩되는 presenter. docs/23_TITLE_SCREEN_BACKLOG.md T4 범위:
    /// 해상도·기본 배속·마스터/효과음 볼륨·언어를 편집하고 <see cref="GameSettingsStore"/>로
    /// 원자적 저장(임시 파일 → rename, 이전 정상본 1개 유지)한다. 여기서 다루는 값은 모두
    /// 게임 규칙에 영향을 주지 않는다(docs/00_TATS_SOURCE_OF_TRUTH.md 구현 경계).
    ///
    /// 언어는 정본에 지원 언어 목록이 없어 "한국어" 한 값만 둔다 — 추가 언어는 계약 미정으로 남긴다.
    /// 상하 화살표로 항목 사이 포커스 이동, 좌우 화살표(또는 값 버튼 클릭·Enter)로 값 변경,
    /// Esc는 T3의 슬롯 목록 화면과 같은 방식으로 이전 화면으로 돌아간다(저장하지 않은 값은 폐기).
    /// </summary>
    public sealed class SettingsPresenter : IDisposable
    {
        const string FocusedClass = "settings__focusable--focused";
        const int VolumeStepPercent = 10;

        readonly VisualElement _root;
        readonly GameSettingsStore _store;

        readonly Button _resolutionButton;
        readonly Button _speedButton;
        readonly Button _masterVolumeButton;
        readonly Button _effectVolumeButton;
        readonly Button _languageButton;
        readonly Label _savedLabel;
        readonly Button _backButton;
        readonly Button _saveButton;

        readonly Button[] _focusOrder;
        int _focusedIndex;
        GameSettings _working;
        bool _disposed;

        /// <summary>`뒤로` 또는 Esc. 저장하지 않은 값은 폐기한다.</summary>
        public event Action Back;

        /// <summary>`저장`이 실제로 파일에 쓴 뒤 발행한다. 실제 적용(해상도 변경 등)은 이 이벤트를 받는 쪽의 몫이다.</summary>
        public event Action<GameSettings> Saved;

        public SettingsPresenter(VisualElement root, GameSettingsStore store)
        {
            _root = root ?? throw new ArgumentNullException(nameof(root));
            _store = store ?? throw new ArgumentNullException(nameof(store));

            _resolutionButton = Resolve<Button>("settings-resolution-value");
            _speedButton = Resolve<Button>("settings-speed-value");
            _masterVolumeButton = Resolve<Button>("settings-master-volume-value");
            _effectVolumeButton = Resolve<Button>("settings-effect-volume-value");
            _languageButton = Resolve<Button>("settings-language-value");
            _savedLabel = Resolve<Label>("settings-saved-label");
            _backButton = Resolve<Button>("settings-back-button");
            _saveButton = Resolve<Button>("settings-save-button");

            _focusOrder = new[]
            {
                _resolutionButton, _speedButton, _masterVolumeButton, _effectVolumeButton,
                _languageButton, _backButton, _saveButton,
            };

            _resolutionButton.clicked += () => AdjustValue(_resolutionButton, 1);
            _speedButton.clicked += () => AdjustValue(_speedButton, 1);
            _masterVolumeButton.clicked += () => AdjustValue(_masterVolumeButton, 1);
            _effectVolumeButton.clicked += () => AdjustValue(_effectVolumeButton, 1);
            _languageButton.clicked += () => AdjustValue(_languageButton, 1);
            _backButton.clicked += RaiseBack;
            _saveButton.clicked += SaveAndReport;

            _root.RegisterCallback<KeyDownEvent>(OnKeyDown, TrickleDown.TrickleDown);

            LoadIntoWorkingCopy();
            SetFocusedIndex(0);
        }

        public void Dispose()
        {
            if (_disposed)
            {
                return;
            }

            _root.UnregisterCallback<KeyDownEvent>(OnKeyDown, TrickleDown.TrickleDown);
            _disposed = true;
        }

        void LoadIntoWorkingCopy()
        {
            var result = _store.Load();
            _working = result.Settings.Clone();
            RefreshLabels();
        }

        void RefreshLabels()
        {
            _resolutionButton.text = FormatResolution(_working.Resolution);
            _speedButton.text = FormatSpeed(_working.DefaultSpeed);
            _masterVolumeButton.text = $"{_working.MasterVolumePercent}%";
            _effectVolumeButton.text = $"{_working.EffectVolumePercent}%";
            _languageButton.text = FormatLanguage(_working.Language);
        }

        static string FormatResolution(SettingsResolution resolution)
        {
            switch (resolution)
            {
                case SettingsResolution.Res1440x900: return "1440×900";
                case SettingsResolution.Res1280x720: return "1280×720";
                default: return resolution.ToString();
            }
        }

        static string FormatSpeed(SettingsDefaultSpeed speed)
        {
            switch (speed)
            {
                case SettingsDefaultSpeed.X1: return "×1";
                case SettingsDefaultSpeed.X3: return "×3";
                case SettingsDefaultSpeed.X5: return "×5";
                default: return speed.ToString();
            }
        }

        static string FormatLanguage(SettingsLanguage language)
        {
            switch (language)
            {
                case SettingsLanguage.Korean: return "한국어";
                default: return language.ToString();
            }
        }

        void AdjustValue(Button target, int direction)
        {
            ClearSavedLabel();

            if (target == _resolutionButton)
            {
                _working.Resolution = CycleEnum(_working.Resolution, direction);
            }
            else if (target == _speedButton)
            {
                _working.DefaultSpeed = CycleEnum(_working.DefaultSpeed, direction);
            }
            else if (target == _masterVolumeButton)
            {
                _working.MasterVolumePercent = ClampPercent(_working.MasterVolumePercent + direction * VolumeStepPercent);
            }
            else if (target == _effectVolumeButton)
            {
                _working.EffectVolumePercent = ClampPercent(_working.EffectVolumePercent + direction * VolumeStepPercent);
            }
            else if (target == _languageButton)
            {
                _working.Language = CycleEnum(_working.Language, direction);
            }

            RefreshLabels();
        }

        static T CycleEnum<T>(T current, int direction) where T : struct, Enum
        {
            var values = (T[])Enum.GetValues(typeof(T));
            var index = Array.IndexOf(values, current);
            if (index < 0)
            {
                index = 0;
            }

            index = ((index + direction) % values.Length + values.Length) % values.Length;
            return values[index];
        }

        static int ClampPercent(int value)
        {
            if (value < 0)
            {
                return 0;
            }

            return value > 100 ? 100 : value;
        }

        void OnKeyDown(KeyDownEvent evt)
        {
            switch (evt.keyCode)
            {
                case KeyCode.DownArrow:
                    SetFocusedIndex((_focusedIndex + 1) % _focusOrder.Length);
                    evt.StopPropagation();
                    break;

                case KeyCode.UpArrow:
                    SetFocusedIndex((_focusedIndex - 1 + _focusOrder.Length) % _focusOrder.Length);
                    evt.StopPropagation();
                    break;

                case KeyCode.LeftArrow:
                    AdjustFocusedValueRow(-1);
                    evt.StopPropagation();
                    break;

                case KeyCode.RightArrow:
                    AdjustFocusedValueRow(1);
                    evt.StopPropagation();
                    break;

                case KeyCode.Return:
                case KeyCode.KeypadEnter:
                    ActivateFocused();
                    evt.StopPropagation();
                    break;

                case KeyCode.Escape:
                    // docs/20 12.1: Esc는 열린 화면을 한 단계 닫는다 — 여기서는 시작 화면으로,
                    // 저장하지 않은 값은 폐기한다(T3의 슬롯 목록 화면 Esc와 같은 방식).
                    RaiseBack();
                    evt.StopPropagation();
                    break;
            }
        }

        void AdjustFocusedValueRow(int direction)
        {
            var focused = _focusOrder[_focusedIndex];
            if (focused == _backButton || focused == _saveButton)
            {
                return;
            }

            AdjustValue(focused, direction);
        }

        void ActivateFocused()
        {
            var focused = _focusOrder[_focusedIndex];
            if (focused == _backButton)
            {
                RaiseBack();
            }
            else if (focused == _saveButton)
            {
                SaveAndReport();
            }
            else
            {
                AdjustValue(focused, 1);
            }
        }

        void SetFocusedIndex(int index)
        {
            _focusOrder[_focusedIndex].RemoveFromClassList(FocusedClass);
            _focusedIndex = index;
            _focusOrder[_focusedIndex].AddToClassList(FocusedClass);
            _focusOrder[_focusedIndex].Focus();
        }

        void ClearSavedLabel()
        {
            _savedLabel.text = string.Empty;
        }

        void RaiseBack()
        {
            Back?.Invoke();
        }

        void SaveAndReport()
        {
            _store.Save(_working);
            _savedLabel.text = "저장했습니다.";
            Saved?.Invoke(_working.Clone());
        }

        T Resolve<T>(string name) where T : VisualElement
        {
            var element = _root.Q<T>(name);
            if (element == null)
            {
                throw new InvalidOperationException($"SettingsScreen.uxml is missing the required element '{name}'.");
            }

            return element;
        }
    }
}
