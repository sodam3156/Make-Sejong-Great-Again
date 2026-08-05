using System;
using UnityEngine;
using UnityEngine.UIElements;

namespace Tats.Game.UI.TitleScreen
{
    /// <summary>
    /// TitleScreen.uxml에 바인딩되는 presenter. 상태 보관과 키보드/클릭 입력 처리만 담당하고,
    /// 메뉴 선택 뒤 실제 화면 전환은 T2~T6 구현 전까지 <see cref="MenuItemActivated"/> 이벤트로만 노출한다.
    /// docs/20_TATS_UX_FRONTEND_HANDOFF_V1.md 8.2절: presenter는 상태 바인딩과 이벤트 연결만 하고
    /// 교통량·포인트·비용을 계산하지 않는다.
    /// </summary>
    public sealed class TitleScreenPresenter : IDisposable
    {
        const string FocusedClass = "title-screen__menu-item--focused";

        static readonly TitleScreenMenuItem[] MenuOrder =
        {
            TitleScreenMenuItem.NewGame,
            TitleScreenMenuItem.Continue,
            TitleScreenMenuItem.Settings,
            TitleScreenMenuItem.Help,
            TitleScreenMenuItem.Credits,
        };

        static readonly string[] MenuButtonNames =
        {
            "new-game-button",
            "continue-button",
            "settings-button",
            "help-button",
            "credits-button",
        };

        readonly VisualElement _root;
        readonly Button[] _menuButtons;
        int _focusedIndex;
        bool _disposed;

        public event Action<TitleScreenMenuItem> MenuItemActivated;

        public TitleScreenPresenter(VisualElement root)
        {
            _root = root ?? throw new ArgumentNullException(nameof(root));
            _menuButtons = new Button[MenuButtonNames.Length];

            for (var i = 0; i < MenuButtonNames.Length; i++)
            {
                var button = _root.Q<Button>(MenuButtonNames[i]);
                if (button == null)
                {
                    throw new InvalidOperationException(
                        $"TitleScreen.uxml is missing the required button '{MenuButtonNames[i]}'.");
                }

                _menuButtons[i] = button;

                var capturedIndex = i;
                button.clicked += () => Activate(capturedIndex);
            }

            _root.RegisterCallback<KeyDownEvent>(OnKeyDown, TrickleDown.TrickleDown);
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

        void OnKeyDown(KeyDownEvent evt)
        {
            switch (evt.keyCode)
            {
                case KeyCode.DownArrow:
                    SetFocusedIndex((_focusedIndex + 1) % _menuButtons.Length);
                    evt.StopPropagation();
                    break;

                case KeyCode.UpArrow:
                    SetFocusedIndex((_focusedIndex - 1 + _menuButtons.Length) % _menuButtons.Length);
                    evt.StopPropagation();
                    break;

                case KeyCode.Return:
                case KeyCode.KeypadEnter:
                    Activate(_focusedIndex);
                    evt.StopPropagation();
                    break;

                case KeyCode.Escape:
                    // docs/20_TATS_UX_FRONTEND_HANDOFF_V1.md 12.1: Esc는 열린 오버레이·모달을 한 단계
                    // 닫고 이전 선택을 보존한다. T1 시작 화면에는 닫을 오버레이·모달이 없으므로
                    // 입력만 흡수하고 포커스는 유지한다. 종료 확인(T7)은 이 항목의 범위 밖이다.
                    evt.StopPropagation();
                    break;
            }
        }

        void SetFocusedIndex(int index)
        {
            _menuButtons[_focusedIndex].RemoveFromClassList(FocusedClass);
            _focusedIndex = index;
            _menuButtons[_focusedIndex].AddToClassList(FocusedClass);
            _menuButtons[_focusedIndex].Focus();
        }

        void Activate(int index)
        {
            SetFocusedIndex(index);
            MenuItemActivated?.Invoke(MenuOrder[index]);
        }
    }
}
